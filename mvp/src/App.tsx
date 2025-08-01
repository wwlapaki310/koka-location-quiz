import React, { useState, useEffect } from 'react';
import { Shuffle, MapPin, CheckCircle, XCircle, Star } from 'lucide-react';

// 型定義
interface SchoolData {
  id: number;
  schoolName: string;
  prefecture: string;
  city: string;
  address: string;
  songTitle: string;
  lyrics: string;
  maskedLyrics: string;
  difficulty: 'easy' | 'medium' | 'hard';
  notes: string;
}

interface QuizQuestion {
  correct: SchoolData;
  choices: SchoolData[];
  maskedLyrics: string;
}

// サンプルデータ（実際のGoogleスプレッドシートの代替）
const sampleData: SchoolData[] = [
  {
    id: 1,
    schoolName: "東京都立新宿高等学校",
    prefecture: "東京都",
    city: "新宿区",
    address: "内藤町11番4号",
    songTitle: "校歌",
    lyrics: "東雲映ゆる富士の嶺を 仰ぎて学ぶ新宿の 健児の意気は雲高く",
    maskedLyrics: "東雲映ゆる富士の嶺を 仰ぎて学ぶ〇〇の 健児の意気は雲高く",
    difficulty: "medium",
    notes: "1921年開校"
  },
  {
    id: 2,
    schoolName: "大阪府立北野高等学校",
    prefecture: "大阪府",
    city: "大阪市淀川区",
    address: "新北野2丁目5番13号",
    songTitle: "校歌",
    lyrics: "淀川清し 北野の 学舎に集う若人の 理想は高く 雲の上",
    maskedLyrics: "〇〇川清し 〇〇の 学舎に集う若人の 理想は高く 雲の上",
    difficulty: "hard",
    notes: "1873年開校"
  },
  {
    id: 3,
    schoolName: "福岡県立修猷館高等学校",
    prefecture: "福岡県",
    city: "福岡市早良区",
    address: "西新2丁目20番1号",
    songTitle: "校歌",
    lyrics: "筑紫野に立つ 修猷館 博多の街を見下ろして 学問の道 歩みゆく",
    maskedLyrics: "〇〇野に立つ 〇〇館 〇〇の街を見下ろして 学問の道 歩みゆく",
    difficulty: "hard",
    notes: "1885年開校"
  },
  {
    id: 4,
    schoolName: "愛知県立旭丘高等学校",
    prefecture: "愛知県",
    city: "名古屋市東区",
    address: "出来町3丁目6番15号",
    songTitle: "校歌",
    lyrics: "名古屋の街に 朝日さし 旭の丘に 学ぶ身の 希望は遠く 空高く",
    maskedLyrics: "〇〇の街に 朝日さし 〇〇の丘に 学ぶ身の 希望は遠く 空高く",
    difficulty: "medium",
    notes: "1906年開校"
  },
  {
    id: 5,
    schoolName: "神奈川県立横浜翠嵐高等学校",
    prefecture: "神奈川県",
    city: "横浜市神奈川区",
    address: "三ツ沢南町1番1号",
    songTitle: "校歌",
    lyrics: "港の見える 丘の上 翠嵐吹きて 青春の 夢は大きく 海を越え",
    maskedLyrics: "港の見える 丘の上 〇〇吹きて 青春の 夢は大きく 海を越え",
    difficulty: "easy",
    notes: "1914年開校"
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

  // 新しい問題を生成
  const generateNewQuestion = () => {
    const question = generateQuestion(sampleData);
    setCurrentQuestion(question);
    setSelectedAnswer(null);
    setShowResult(false);
  };

  // ゲーム開始
  const startGame = () => {
    setScore(0);
    setQuestionCount(0);
    setGameState('playing');
    generateNewQuestion();
  };

  // 回答処理
  const handleAnswer = (selected: SchoolData) => {
    setSelectedAnswer(selected);
    setShowResult(true);
    
    if (selected.id === currentQuestion?.correct.id) {
      setScore(score + 1);
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
            <h2 className="text-lg font-semibold text-gray-800 mb-4">ゲームルール</h2>
            <ul className="text-sm text-gray-600 space-y-2 text-left">
              <li>• 5問のクイズに挑戦</li>
              <li>• 校歌の歌詞（学校名は〇〇で隠されています）</li>
              <li>• 4つの選択肢から正しい学校を選択</li>
              <li>• 難易度：初級、中級、上級</li>
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
            <div className="text-6xl font-bold text-blue-600 mb-2">{score}/5</div>
            <p className="text-lg text-gray-600">
              {score === 5 ? '完璧です！' : 
               score >= 3 ? 'よくできました！' : 
               score >= 1 ? 'もう少し頑張りましょう！' : 
               '次回頑張ってください！'}
            </p>
          </div>
          
          <div className="mb-8 p-6 bg-gray-50 rounded-xl">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-gray-500">正解率</div>
                <div className="text-xl font-bold text-green-600">{Math.round((score / 5) * 100)}%</div>
              </div>
              <div>
                <div className="text-gray-500">問題数</div>
                <div className="text-xl font-bold text-blue-600">5問</div>
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
      <div className="max-w-4xl mx-auto">
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
              <span>スコア {score}/{questionCount + 1}</span>
            </div>
          </div>
        </div>

        {/* 問題カード */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-gray-800 mb-2">校歌の歌詞</h2>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-gray-700 leading-relaxed text-center">
                「{currentQuestion.maskedLyrics}」
              </p>
            </div>
          </div>
          <p className="text-sm text-gray-600 text-center">
            この校歌はどの学校のものでしょうか？
          </p>
        </div>

        {/* 選択肢 */}
        <div className="grid gap-4 mb-6">
          {currentQuestion.choices.map((choice, index) => (
            <button
              key={choice.id}
              onClick={() => !showResult && handleAnswer(choice)}
              disabled={showResult}
              className={`bg-white rounded-xl shadow-lg p-4 text-left transition-all hover:shadow-xl ${
                showResult 
                  ? choice.id === currentQuestion.correct.id
                    ? 'ring-2 ring-green-500 bg-green-50'
                    : selectedAnswer?.id === choice.id
                      ? 'ring-2 ring-red-500 bg-red-50'
                      : 'opacity-60'
                  : 'hover:bg-gray-50'
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

        {/* 結果表示 */}
        {showResult && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <div className="text-center mb-4">
              {selectedAnswer?.id === currentQuestion.correct.id ? (
                <div className="text-green-600">
                  <CheckCircle className="w-12 h-12 mx-auto mb-2" />
                  <h3 className="text-xl font-bold">正解です！</h3>
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