import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { Shuffle, MapPin, CheckCircle, XCircle, Star, HelpCircle, Eye, Map } from 'lucide-react';

// 拡張データのインポート
import { extendedSchoolData, type SchoolData } from './data/extendedSchoolData';

// Leafletアイコンの修正（Viteの問題対応）
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface QuizQuestion {
  correct: SchoolData;
  choices: SchoolData[];
  maskedLyrics: string;
}

// 地図クリックハンドラーコンポーネント
function MapClickHandler({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click: (e) => {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

// クイズロジック
const generateQuestion = (data: SchoolData[]): QuizQuestion => {
  const correct = data[Math.floor(Math.random() * data.length)];
  const otherChoices = data.filter(school => school.id !== correct.id);
  
  // 他の選択肢をランダムに3つ選択
  const shuffled = otherChoices.sort(() => 0.5 - Math.random());
  const choices = [correct, ...shuffled.slice(0, 3)].sort(() => 0.5 - Math.random());
  
  return {
    correct,
    choices,
    maskedLyrics: correct.maskedLyrics
  };
};

// 地図上の距離計算（キロメートル）
const calculateDistance = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
  const R = 6371; // 地球の半径（キロメートル）
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
};

// 難易度に応じた色
const getDifficultyColor = (difficulty: string) => {
  switch (difficulty) {
    case 'easy': return 'text-green-600 bg-green-100';
    case 'medium': return 'text-yellow-600 bg-yellow-100';
    case 'hard': return 'text-red-600 bg-red-100';
    default: return 'text-gray-600 bg-gray-100';
  }
};

const getDifficultyText = (difficulty: string) => {
  switch (difficulty) {
    case 'easy': return '初級';
    case 'medium': return '中級';
    case 'hard': return '上級';
    default: return '不明';
  }
};

export default function App() {
  const [currentQuestion, setCurrentQuestion] = useState<QuizQuestion | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<SchoolData | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [questionCount, setQuestionCount] = useState(0);
  const [gameState, setGameState] = useState<'ready' | 'playing' | 'finished'>('ready');
  
  // UI表示状態
  const [showFullLyrics, setShowFullLyrics] = useState(false);
  const [hintsUsed, setHintsUsed] = useState<number>(0);
  const [showHints, setShowHints] = useState<boolean[]>([false, false, false]);
  
  // 地図関連の状態
  const [clickedPosition, setClickedPosition] = useState<{lat: number, lng: number} | null>(null);
  const [mapAnswerMode, setMapAnswerMode] = useState<boolean>(false);

  // 新しい問題を生成
  const generateNewQuestion = () => {
    const question = generateQuestion(extendedSchoolData); // 拡張データを使用
    setCurrentQuestion(question);
    setSelectedAnswer(null);
    setShowResult(false);
    setShowFullLyrics(false);
    setHintsUsed(0);
    setShowHints([false, false, false]);
    setClickedPosition(null);
    setMapAnswerMode(false);
  };

  // ゲーム開始
  const startGame = () => {
    setScore(0);
    setQuestionCount(0);
    setGameState('playing');
    generateNewQuestion();
  };

  // ヒント表示
  const showHint = (hintIndex: number) => {
    if (!showHints[hintIndex]) {
      const newShowHints = [...showHints];
      newShowHints[hintIndex] = true;
      setShowHints(newShowHints);
      
      if (hintsUsed === hintIndex) {
        setHintsUsed(hintIndex + 1);
      }
    }
  };

  // スコア計算（ヒント使用で減点）
  const calculateScore = (isMapAnswer: boolean = false) => {
    const baseScore = 100;
    let penalty = hintsUsed * 20; // ヒント1つにつき20点減点
    
    // 地図で正解した場合はボーナス
    if (isMapAnswer) {
      penalty -= 20; // 地図回答ボーナス
    }
    
    return Math.max(baseScore - penalty, 20); // 最低20点
  };

  // 地図クリック処理
  const handleMapClick = (lat: number, lng: number) => {
    if (!currentQuestion || showResult) return;
    
    setClickedPosition({ lat, lng });
    const distance = calculateDistance(
      lat, lng, 
      currentQuestion.correct.coordinates.lat, 
      currentQuestion.correct.coordinates.lng
    );
    
    // 50km以内なら正解とする
    const isCorrect = distance <= 50;
    
    if (isCorrect) {
      setSelectedAnswer(currentQuestion.correct);
      setShowResult(true);
      setScore(score + calculateScore(true));
    } else {
      // 地図で不正解の場合、少し待ってからリセット
      setTimeout(() => {
        setClickedPosition(null);
      }, 2000);
    }
  };

  // 選択肢による回答処理
  const handleAnswer = (selected: SchoolData) => {
    setSelectedAnswer(selected);
    setShowResult(true);
    
    if (selected.id === currentQuestion?.correct.id) {
      setScore(score + calculateScore(false));
    }
  };

  // 次の問題
  const nextQuestion = () => {
    const newCount = questionCount + 1;
    setQuestionCount(newCount);
    
    if (newCount >= 5) {
      setGameState('finished');
    } else {
      generateNewQuestion();
    }
  };

  // ゲーム初期化
  useEffect(() => {
    generateNewQuestion();
  }, []);

  if (gameState === 'ready') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-lg w-full text-center">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">校歌場所当てクイズ</h1>
            <p className="text-gray-600">校歌の歌詞から学校を推測してください！</p>
          </div>
          
          <div className="mb-8 p-6 bg-gray-50 rounded-xl">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">🎉 データ大幅拡張！</h2>
            <ul className="text-sm text-gray-600 space-y-2 text-left">
              <li>📊 <strong>20校のデータ</strong>：全国各地から厳選</li>
              <li>🗾 <strong>全国網羅</strong>：北海道から沖縄まで</li>
              <li>📖 <strong>校歌全文表示</strong>：学校名も含む完全版</li>
              <li>🗺️ <strong>地図回答機能</strong>：地図上をクリックして回答</li>
              <li>💡 <strong>段階的ヒント機能</strong>：困ったらヒントを活用</li>
              <li>📊 <strong>スコア調整</strong>：地図回答でボーナス、ヒント使用で減点</li>
            </ul>
          </div>
          
          <div className="mb-6 p-4 bg-blue-50 rounded-xl">
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="font-bold text-green-600">10校</div>
                <div className="text-gray-600">初級</div>
              </div>
              <div>
                <div className="font-bold text-yellow-600">9校</div>
                <div className="text-gray-600">中級</div>
              </div>
              <div>
                <div className="font-bold text-red-600">1校</div>
                <div className="text-gray-600">上級</div>
              </div>
            </div>
          </div>
          
          <button
            onClick={startGame}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-xl transition-colors flex items-center gap-2 mx-auto"
          >
            <Star className="w-5 h-5" />
            ゲーム開始
          </button>
        </div>
      </div>
    );
  }

  if (gameState === 'finished') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-lg w-full text-center">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-800 mb-4">ゲーム終了！</h1>
            <div className="text-6xl font-bold text-blue-600 mb-2">{score}/500</div>
            <p className="text-lg text-gray-600">
              {score >= 400 ? '素晴らしい！日本地理マスター！' : 
               score >= 300 ? 'よくできました！地理の知識豊富ですね' : 
               score >= 200 ? '健闘しました！もう少し頑張りましょう' : 
               'お疲れ様でした！次回に期待！'}
            </p>
          </div>
          
          <div className="mb-8 p-6 bg-gray-50 rounded-xl">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-gray-500">最終スコア</div>
                <div className="text-xl font-bold text-green-600">{score}点</div>
              </div>
              <div>
                <div className="text-gray-500">平均スコア</div>
                <div className="text-xl font-bold text-blue-600">{Math.round(score/5)}点/問</div>
              </div>
            </div>
            
            <div className="mt-4 text-center">
              <div className="text-xs text-gray-500 mb-1">あなたのレベル</div>
              <div className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${
                score >= 400 ? 'bg-purple-100 text-purple-800' :
                score >= 300 ? 'bg-blue-100 text-blue-800' :
                score >= 200 ? 'bg-green-100 text-green-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {score >= 400 ? '🏆 校歌マスター' :
                 score >= 300 ? '🥇 地理博士' :
                 score >= 200 ? '🥈 地理探検家' :
                 '🥉 地理チャレンジャー'}
              </div>
            </div>
          </div>
          
          <button
            onClick={() => setGameState('ready')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-xl transition-colors flex items-center gap-2 mx-auto"
          >
            <Shuffle className="w-5 h-5" />
            もう一度プレイ
          </button>
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">問題を読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* ヘッダー */}
        <div className="bg-white rounded-xl shadow-lg p-4 mb-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-gray-800">校歌場所当てクイズ</h1>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getDifficultyColor(currentQuestion.correct.difficulty)}`}>
                {getDifficultyText(currentQuestion.correct.difficulty)}
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>問題 {questionCount + 1}/5</span>
              <span>スコア {score}点</span>
              <span>ヒント使用 {hintsUsed}/3</span>
            </div>
          </div>
        </div>

        {/* メインコンテンツエリア */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* 左側：歌詞表示エリア */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-800">校歌の歌詞</h2>
              <button
                onClick={() => setShowFullLyrics(!showFullLyrics)}
                className="flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm hover:bg-blue-200 transition-colors"
              >
                <Eye className="w-4 h-4" />
                {showFullLyrics ? '一部表示' : '全文表示'}
              </button>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <p className="text-gray-700 leading-relaxed text-center text-lg">
                「{showFullLyrics ? currentQuestion.correct.lyrics : currentQuestion.maskedLyrics}」
              </p>
            </div>
            
            <p className="text-sm text-gray-600 text-center mb-4">
              この校歌はどの学校のものでしょうか？
            </p>
            
            <div className="text-center">
              <button
                onClick={() => setMapAnswerMode(!mapAnswerMode)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium mx-auto transition-colors ${
                  mapAnswerMode 
                    ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                    : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }`}
              >
                <Map className="w-4 h-4" />
                {mapAnswerMode ? '地図回答モード（ON）' : '地図で回答する'}
              </button>
            </div>
          </div>

          {/* 右側：地図エリア */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Map className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-800">日本地図</h2>
              {mapAnswerMode && (
                <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                  地図をクリックして回答
                </span>
              )}
            </div>
            
            <div className="h-80 rounded-lg overflow-hidden">
              <MapContainer
                center={[36.5, 138]}
                zoom={5}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                
                {mapAnswerMode && !showResult && (
                  <MapClickHandler onMapClick={handleMapClick} />
                )}
                
                {/* クリックした位置にマーカー表示 */}
                {clickedPosition && (
                  <Marker position={[clickedPosition.lat, clickedPosition.lng]}>
                    <Popup>
                      クリックした位置<br />
                      ({clickedPosition.lat.toFixed(4)}, {clickedPosition.lng.toFixed(4)})
                    </Popup>
                  </Marker>
                )}
                
                {/* 結果表示時に正解の学校位置を表示 */}
                {showResult && (
                  <Marker position={[currentQuestion.correct.coordinates.lat, currentQuestion.correct.coordinates.lng]}>
                    <Popup>
                      <strong>{currentQuestion.correct.schoolName}</strong><br />
                      {currentQuestion.correct.prefecture} {currentQuestion.correct.city}
                    </Popup>
                  </Marker>
                )}
              </MapContainer>
            </div>
            
            {mapAnswerMode && !showResult && (
              <p className="text-sm text-gray-600 text-center mt-2">
                💡 学校がありそうな場所を地図上でクリックしてください（50km以内で正解）
              </p>
            )}
          </div>
        </div>

        {/* ヒント機能 */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <HelpCircle className="w-5 h-5" />
            ヒント機能
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => showHint(0)}
              className={`p-4 rounded-lg border-2 transition-all ${
                showHints[0] 
                  ? 'border-blue-300 bg-blue-50' 
                  : 'border-gray-200 hover:border-blue-200 hover:bg-blue-50'
              }`}
            >
              <div className="text-sm font-medium text-gray-800 mb-2">
                ヒント1: 地方 {!showHints[0] && '(-20点)'}
              </div>
              <div className="text-sm text-gray-600">
                {showHints[0] ? currentQuestion.correct.hints.prefecture : '？？？'}
              </div>
            </button>

            <button
              onClick={() => showHint(1)}
              className={`p-4 rounded-lg border-2 transition-all ${
                showHints[1] 
                  ? 'border-blue-300 bg-blue-50' 
                  : 'border-gray-200 hover:border-blue-200 hover:bg-blue-50'
              }`}
            >
              <div className="text-sm font-medium text-gray-800 mb-2">
                ヒント2: 地域 {!showHints[1] && '(-40点)'}
              </div>
              <div className="text-sm text-gray-600">
                {showHints[1] ? currentQuestion.correct.hints.region : '？？？'}
              </div>
            </button>

            <button
              onClick={() => showHint(2)}
              className={`p-4 rounded-lg border-2 transition-all ${
                showHints[2] 
                  ? 'border-blue-300 bg-blue-50' 
                  : 'border-gray-200 hover:border-blue-200 hover:bg-blue-50'
              }`}
            >
              <div className="text-sm font-medium text-gray-800 mb-2">
                ヒント3: 特徴 {!showHints[2] && '(-60点)'}
              </div>
              <div className="text-sm text-gray-600">
                {showHints[2] ? currentQuestion.correct.hints.landmark : '？？？'}
              </div>
            </button>
          </div>
        </div>

        {/* 選択肢（4択） */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">または選択肢から選ぶ</h3>
          
          <div className="grid gap-3">
            {currentQuestion.choices.map((choice, index) => (
              <button
                key={choice.id}
                onClick={() => !showResult && handleAnswer(choice)}
                disabled={showResult}
                className={`bg-white rounded-xl border-2 p-4 text-left transition-all hover:shadow-md ${ 
                  showResult 
                    ? choice.id === currentQuestion.correct.id
                      ? 'border-green-500 bg-green-50'
                      : selectedAnswer?.id === choice.id
                        ? 'border-red-500 bg-red-50'
                        : 'border-gray-200 opacity-60'
                    : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-semibold text-gray-800 mb-1">
                      {String.fromCharCode(65 + index)}. {choice.schoolName}
                    </div>
                    <div className="text-sm text-gray-600 flex items-center gap-2">
                      <MapPin className="w-4 h-4" />
                      {choice.prefecture} {choice.city}
                    </div>
                  </div>
                  {showResult && choice.id === currentQuestion.correct.id && (
                    <CheckCircle className="w-6 h-6 text-green-500" />
                  )}
                  {showResult && selectedAnswer?.id === choice.id && choice.id !== currentQuestion.correct.id && (
                    <XCircle className="w-6 h-6 text-red-500" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* 結果表示 */}
        {showResult && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <div className="text-center mb-4">
              {selectedAnswer?.id === currentQuestion.correct.id ? (
                <div className="text-green-600">
                  <CheckCircle className="w-12 h-12 mx-auto mb-2" />
                  <h3 className="text-xl font-bold">正解です！</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    獲得スコア: {calculateScore(clickedPosition !== null)}点 
                    {clickedPosition && ' (地図回答ボーナス)'}
                    {hintsUsed > 0 && ` (ヒント${hintsUsed}個使用)`}
                  </p>
                </div>
              ) : (
                <div className="text-red-600">
                  <XCircle className="w-12 h-12 mx-auto mb-2" />
                  <h3 className="text-xl font-bold">不正解</h3>
                  <p className="text-gray-600 mt-2">
                    正解は「{currentQuestion.correct.schoolName}」でした
                  </p>
                </div>
              )}
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <h4 className="font-semibold text-gray-800 mb-2">学校情報</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-600">
                <div>📍 {currentQuestion.correct.prefecture} {currentQuestion.correct.city}</div>
                <div>🏫 {currentQuestion.correct.schoolName}</div>
                <div>🌐 座標: {currentQuestion.correct.coordinates.lat}, {currentQuestion.correct.coordinates.lng}</div>
                <div className="md:col-span-2">📝 {currentQuestion.correct.notes}</div>
              </div>
            </div>

            <button
              onClick={nextQuestion}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-xl transition-colors"
            >
              {questionCount + 1 >= 5 ? '結果を見る' : '次の問題'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
