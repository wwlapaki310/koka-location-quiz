import React, { useState, useEffect } from 'react';
import { Shuffle, MapPin, CheckCircle, XCircle, Star, HelpCircle, Eye, Map } from 'lucide-react';

// 型定義
interface SchoolData {
  id: number;
  schoolName: string;
  prefecture: string;
  city: string;
  address: string;
  coordinates: {
    lat: number;
    lng: number;
  };
  songTitle: string;
  lyrics: string;           // 全文歌詞
  maskedLyrics: string;     // マスク済み歌詞
  difficulty: 'easy' | 'medium' | 'hard';
  notes: string;
  hints: {
    prefecture: string;     // 都道府県ヒント
    region: string;         // 地域ヒント
    landmark: string;       // 地理的特徴ヒント
  };
}

interface QuizQuestion {
  correct: SchoolData;
  choices: SchoolData[];
  maskedLyrics: string;
}

// 拡張されたサンプルデータ
const sampleData: SchoolData[] = [
  {
    id: 1,
    schoolName: "東京都立戸山高等学校",
    prefecture: "東京都",
    city: "新宿区",
    address: "戸山3-19-1",
    coordinates: { lat: 35.7019, lng: 139.7174 },
    songTitle: "校歌",
    lyrics: "朝日輝く戸山の丘に 学び舎建てて百年余り 若き血潮は雲を呼びつつ 理想の峰を目指しゆく われら誇らん戸山健児",
    maskedLyrics: "朝日輝く〇〇の丘に 学び舎建てて百年余り 若き血潮は雲を呼びつつ 理想の峰を目指しゆく われら誇らん〇〇健児",
    difficulty: "medium",
    notes: "1888年開校の伝統校",
    hints: {
      prefecture: "関東地方の中心都市",
      region: "山手線内側の文教地区",
      landmark: "早稲田大学に近い高台の住宅地"
    }
  },
  {
    id: 2,
    schoolName: "大阪府立北野高等学校",
    prefecture: "大阪府",
    city: "大阪市淀川区",
    address: "新北野2-5-13",
    coordinates: { lat: 34.7209, lng: 135.4606 },
    songTitle: "校歌",
    lyrics: "淀川清く流るる岸辺 北野の丘に学び舎あり 自由闊達の気風を受けて 真理探究に励みけり われら北野の誇りもて",
    maskedLyrics: "〇〇川清く流るる岸辺 〇〇の丘に学び舎あり 自由闊達の気風を受けて 真理探究に励みけり われら〇〇の誇りもて",
    difficulty: "hard",
    notes: "1873年開校、関西屈指の進学校",
    hints: {
      prefecture: "関西地方の中心府",
      region: "大きな川が流れる北部地域",
      landmark: "大阪市北部、淀川沿いの文教地区"
    }
  },
  {
    id: 3,
    schoolName: "福岡県立修猷館高等学校",
    prefecture: "福岡県",
    city: "福岡市早良区",
    address: "西新2-20-1",
    coordinates: { lat: 33.5847, lng: 130.3558 },
    songTitle: "校歌",
    lyrics: "筑紫野に立つ修猷館 博多の街を見下ろして 文武両道の道を歩み 九州男児の意気高し われら修猷の伝統を",
    maskedLyrics: "〇〇野に立つ〇〇館 〇〇の街を見下ろして 文武両道の道を歩み 九州男児の意気高し われら〇〇の伝統を",
    difficulty: "hard",
    notes: "1885年開校、九州の名門校",
    hints: {
      prefecture: "九州北部の中心県",
      region: "古くから大陸との交流拠点",
      landmark: "福岡市西部、海に近い文教地区"
    }
  },
  {
    id: 4,
    schoolName: "愛知県立旭丘高等学校",
    prefecture: "愛知県",
    city: "名古屋市東区",
    address: "出来町3-6-15",
    coordinates: { lat: 35.1851, lng: 136.9348 },
    songTitle: "校歌",
    lyrics: "名古屋城下の旭丘 朝日さしそう学び舎に 尾張平野を見渡して 中部の雄たる意気を持ち われら旭丘健児なり",
    maskedLyrics: "〇〇城下の〇〇丘 朝日さしそう学び舎に 〇〇平野を見渡して 中部の雄たる意気を持ち われら〇〇健児なり",
    difficulty: "medium",
    notes: "1906年開校、中部地方の名門校",
    hints: {
      prefecture: "中部地方の中心県",
      region: "戦国時代の有力武将の拠点",
      landmark: "名古屋市中心部、城の近くの丘陵地"
    }
  },
  {
    id: 5,
    schoolName: "神奈川県立横浜翠嵐高等学校",
    prefecture: "神奈川県",
    city: "横浜市神奈川区",
    address: "三ツ沢南町1-1",
    coordinates: { lat: 35.4758, lng: 139.6136 },
    songTitle: "校歌",
    lyrics: "港の見える丘の上 翠嵐吹きて青春の 夢は大きく海を越え 国際都市の風受けて われら翠嵐誇らん",
    maskedLyrics: "港の見える丘の上 〇〇吹きて青春の 夢は大きく海を越え 国際都市の風受けて われら〇〇誇らん",
    difficulty: "easy",
    notes: "1914年開校、国際港都の名門校",
    hints: {
      prefecture: "関東地方南部の県",
      region: "国際的な港湾都市",
      landmark: "横浜港を見下ろす高台の住宅地"
    }
  }
];

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

  // 新しい問題を生成
  const generateNewQuestion = () => {
    const question = generateQuestion(sampleData);
    setCurrentQuestion(question);
    setSelectedAnswer(null);
    setShowResult(false);
    setShowFullLyrics(false);
    setHintsUsed(0);
    setShowHints([false, false, false]);
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
  const calculateScore = () => {
    const baseScore = 100;
    const penalty = hintsUsed * 20; // ヒント1つにつき20点減点
    return Math.max(baseScore - penalty, 20); // 最低20点
  };

  // 回答処理
  const handleAnswer = (selected: SchoolData) => {
    setSelectedAnswer(selected);
    setShowResult(true);
    
    if (selected.id === currentQuestion?.correct.id) {
      setScore(score + calculateScore());
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
            <h2 className="text-lg font-semibold text-gray-800 mb-4">新機能追加！</h2>
            <ul className="text-sm text-gray-600 space-y-2 text-left">
              <li>📖 <strong>校歌全文表示</strong>：学校名も含む完全版が読める</li>
              <li>💡 <strong>段階的ヒント機能</strong>：困ったらヒントを活用</li>
              <li>📊 <strong>スコア調整</strong>：ヒント使用で減点あり</li>
              <li>🗺️ <strong>地図機能（近日追加予定）</strong></li>
            </ul>
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
              {score >= 400 ? '完璧です！' : 
               score >= 300 ? 'よくできました！' : 
               score >= 200 ? 'もう少し頑張りましょう！' : 
               '次回頑張ってください！'}
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
      <div className="max-w-6xl mx-auto">
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
              <p className="text-gray-700 leading-relaxed text-center">
                「{showFullLyrics ? currentQuestion.correct.lyrics : currentQuestion.maskedLyrics}」
              </p>
            </div>
            
            <p className="text-sm text-gray-600 text-center">
              この校歌はどの学校のものでしょうか？
            </p>
          </div>

          {/* 右側：地図エリア（今後実装予定） */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Map className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-800">地図表示</h2>
              <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs">近日実装</span>
            </div>
            
            <div className="bg-gray-100 rounded-lg h-64 flex items-center justify-center">
              <div className="text-center text-gray-500">
                <Map className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">日本地図による回答機能</p>
                <p className="text-xs">次のバージョンで実装予定</p>
              </div>
            </div>
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

        {/* 選択肢（4択をヒント的な位置に） */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">選択肢から選ぶ</h3>
          
          <div className="grid gap-4">
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
                    獲得スコア: {calculateScore()}点 {hintsUsed > 0 && `(ヒント${hintsUsed}個使用)`}
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