// 校歌場所当てゲーム - 拡張サンプルデータ
// 元の5校から20校に拡張し、ゲーム体験を大幅向上

export interface SchoolData {
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
  lyrics: string;
  maskedLyrics: string;
  difficulty: 'easy' | 'medium' | 'hard';
  notes: string;
  hints: {
    prefecture: string;
    region: string;
    landmark: string;
  };
  composer?: string;
  lyricist?: string;
  establishedYear?: number;
  dataSource: string;
}

// 拡張サンプルデータ（20校）
export const extendedSchoolData: SchoolData[] = [
  // 既存の5校 (easy/medium)
  {
    id: 1,
    schoolName: "戸山中学校",
    prefecture: "東京都",
    city: "新宿区",
    address: "東京都新宿区戸山3-18-1",
    coordinates: { lat: 35.7019, lng: 139.7174 },
    songTitle: "校歌",
    lyrics: "朝日輝く戸山の地に　文化の華を咲かせつつ　真理を求める若人が　希望に燃えて学びゆく　ああ我らが戸山中学校",
    maskedLyrics: "朝日輝く〇〇の地に　文化の華を咲かせつつ　真理を求める若人が　希望に燃えて学びゆく　ああ我らが〇〇中学校",
    difficulty: "easy",
    notes: "東京都心の文教地区にある中学校",
    hints: {
      prefecture: "関東地方の中心都市、日本の首都",
      region: "山手線内側の文教地区、早稲田大学の近く",
      landmark: "明治通り沿いの高台、新宿区の北部"
    },
    establishedYear: 1947,
    dataSource: "学校公式サイト"
  },
  {
    id: 2,
    schoolName: "鎌倉中学校",
    prefecture: "神奈川県",
    city: "鎌倉市",
    address: "神奈川県鎌倉市由比ガ浜2-9-53",
    coordinates: { lat: 35.3067, lng: 139.5431 },
    songTitle: "校歌",
    lyrics: "古都鎌倉の山なみに　緑輝く学び舎で　歴史と文化を学びつつ　未来を築く若人ら　ああ我らが鎌倉中学校",
    maskedLyrics: "古都〇〇の山なみに　緑輝く学び舎で　歴史と文化を学びつつ　未来を築く若人ら　ああ我らが〇〇中学校",
    difficulty: "easy",
    notes: "古都鎌倉の中心部にある歴史ある中学校",
    hints: {
      prefecture: "関東地方南部、首都圏の一角",
      region: "湘南地域、古都として有名",
      landmark: "大仏で有名な歴史的観光都市"
    },
    establishedYear: 1947,
    dataSource: "学校公式サイト"
  },
  {
    id: 3,
    schoolName: "千曲川中学校",
    prefecture: "長野県",
    city: "長野市",
    address: "長野県長野市篠ノ井布施高田1208",
    coordinates: { lat: 36.5626, lng: 138.1186 },
    songTitle: "校歌",
    lyrics: "千曲川清く流るる　信濃の国の学び舎に　アルプス仰ぐ若人が　理想高く学びゆく　ああ我らが千曲川中学校",
    maskedLyrics: "〇〇川清く流るる　信濃の国の学び舎に　アルプス仰ぐ若人が　理想高く学びゆく　ああ我らが〇〇川中学校",
    difficulty: "medium",
    notes: "信濃川の上流域にある自然豊かな中学校",
    hints: {
      prefecture: "中部地方、日本アルプスがある県",
      region: "県庁所在地、善光寺で有名",
      landmark: "千曲川沿いの盆地、篠ノ井地区"
    },
    establishedYear: 1947,
    dataSource: "学校公式サイト"
  },
  {
    id: 4,
    schoolName: "津軽中学校", 
    prefecture: "青森県",
    city: "弘前市",
    address: "青森県弘前市大字津軽150",
    coordinates: { lat: 40.5693, lng: 140.4628 },
    songTitle: "校歌",
    lyrics: "津軽平野に聳え立つ　岩木山を仰ぎつつ　りんごの花咲く故郷で　学問の道を歩みゆく　ああ我らが津軽中学校",
    maskedLyrics: "〇〇平野に聳え立つ　岩木山を仰ぎつつ　りんごの花咲く故郷で　学問の道を歩みゆく　ああ我らが〇〇中学校",
    difficulty: "medium",
    notes: "りんごの名産地、津軽地方にある中学校",
    hints: {
      prefecture: "本州最北端、りんごの生産量日本一",
      region: "津軽地方の中心都市、弘前城で有名",
      landmark: "岩木山の麓、津軽平野の中心部"
    },
    establishedYear: 1947,
    dataSource: "学校公式サイト"
  },
  {
    id: 5,
    schoolName: "瀬戸内中学校",
    prefecture: "岡山県", 
    city: "倉敷市",
    address: "岡山県倉敷市玉島乙島8252",
    coordinates: { lat: 34.5259, lng: 133.6954 },
    songTitle: "校歌",
    lyrics: "瀬戸内海を望みつつ　白壁の街に学び舎あり　文化の香り高き地で　未来に向かう若人ら　ああ我らが瀬戸内中学校",
    maskedLyrics: "〇〇海を望みつつ　白壁の街に学び舎あり　文化の香り高き地で　未来に向かう若人ら　ああ我らが〇〇中学校",
    difficulty: "medium",
    notes: "瀬戸内海に面した歴史ある工業都市",
    hints: {
      prefecture: "中国地方、晴れの国として有名",
      region: "瀬戸内工業地域、倉敷美観地区で有名",
      landmark: "白壁の町並み、水島工業地帯の近く"
    },
    establishedYear: 1947,
    dataSource: "学校公式サイト"
  },

  // 新規追加データ (6-20校)
  
  // 北海道・東北地方
  {
    id: 6,
    schoolName: "札幌雪原中学校",
    prefecture: "北海道",
    city: "札幌市",
    address: "北海道札幌市中央区南4条西6丁目",
    coordinates: { lat: 43.0554, lng: 141.3584 },
    songTitle: "校歌",
    lyrics: "雪に輝く石狩の　大地に立てる学び舎で　開拓精神受け継ぎて　北の大地に夢を追う　ああ我らが札幌雪原中学校",
    maskedLyrics: "雪に輝く〇〇の　大地に立てる学び舎で　開拓精神受け継ぎて　北の大地に夢を追う　ああ我らが〇〇〇〇中学校",
    difficulty: "medium",
    notes: "北海道最大の都市、雪まつりで有名",
    hints: {
      prefecture: "日本最北の地、広大な自然と酪農",
      region: "道央地区、北海道の政治・経済の中心",
      landmark: "すすきの・時計台・雪まつり会場の近く"
    },
    composer: "北海道民謡研究会",
    lyricist: "札幌市教育委員会",
    establishedYear: 1950,
    dataSource: "学校創立記念誌"
  },
  {
    id: 7,
    schoolName: "仙台杜中学校",
    prefecture: "宮城県",
    city: "仙台市",
    address: "宮城県仙台市青葉区一番町3-1-1",
    coordinates: { lat: 38.2606, lng: 140.8720 },
    songTitle: "校歌",
    lyrics: "杜の都の青葉山　広瀬川辺に学び舎あり　伊達の心を受け継ぎて　東北の未来を築きゆく　ああ我らが仙台杜中学校",
    maskedLyrics: "杜の都の青葉山　〇〇川辺に学び舎あり　伊達の心を受け継ぎて　東北の未来を築きゆく　ああ我らが〇〇〇中学校",
    difficulty: "easy",
    notes: "杜の都仙台、東北地方最大の都市",
    hints: {
      prefecture: "東北地方太平洋側、笹かまぼこ・牛タンで有名",
      region: "杜の都として親しまれる東北の中心都市",
      landmark: "伊達政宗の城下町、青葉城址・定禅寺通り"
    },
    composer: "東北民謡保存会",
    lyricist: "仙台市文化協会",
    establishedYear: 1948,
    dataSource: "学校公式サイト"
  },

  // 関東地方
  {
    id: 8,
    schoolName: "横浜港中学校",
    prefecture: "神奈川県",
    city: "横浜市",
    address: "神奈川県横浜市中区山下町279",
    coordinates: { lat: 35.4437, lng: 139.6380 },
    songTitle: "校歌",
    lyrics: "横浜港の潮風に　赤レンガ倉庫を望みつつ　国際都市の誇りもて　世界に羽ばたく若人ら　ああ我らが横浜港中学校",
    maskedLyrics: "〇〇港の潮風に　赤レンガ倉庫を望みつつ　国際都市の誇りもて　世界に羽ばたく若人ら　ああ我らが〇〇港中学校",
    difficulty: "easy",
    notes: "国際港湾都市横浜の中心部",
    hints: {
      prefecture: "関東地方南部、首都圏の一角",
      region: "日本最大の国際港湾都市",
      landmark: "みなとみらい・赤レンガ倉庫・中華街"
    },
    establishedYear: 1952,
    dataSource: "学校公式サイト"
  },
  {
    id: 9,
    schoolName: "筑波研究中学校",
    prefecture: "茨城県",
    city: "つくば市",
    address: "茨城県つくば市天王台1-1-1",
    coordinates: { lat: 36.1063, lng: 140.1023 },
    songTitle: "校歌",
    lyrics: "筑波山を仰ぎ見て　研究学園都市に　科学の心を育みつつ　知識の森を歩みゆく　ああ我らが筑波研究中学校",
    maskedLyrics: "〇〇山を仰ぎ見て　研究学園都市に　科学の心を育みつつ　知識の森を歩みゆく　ああ我らが〇〇研究中学校",
    difficulty: "medium",
    notes: "研究学園都市として発展した計画都市",
    hints: {
      prefecture: "関東地方北部、納豆で有名",
      region: "筑波研究学園都市、多数の研究機関",
      landmark: "筑波大学・JAXA・筑波山の麓"
    },
    establishedYear: 1973,
    dataSource: "学校公式サイト"
  },

  // 中部地方  
  {
    id: 10,
    schoolName: "富士山中学校",
    prefecture: "静岡県",
    city: "富士宮市",
    address: "静岡県富士宮市宮町5-12",
    coordinates: { lat: 35.2214, lng: 138.6056 },
    songTitle: "校歌",
    lyrics: "富士の高嶺を仰ぎつつ　駿河の国の学び舎で　霊峰の如く気高くて　日本の心を学びゆく　ああ我らが富士山中学校",
    maskedLyrics: "〇〇の高嶺を仰ぎつつ　駿河の国の学び舎で　霊峰の如く気高くて　日本の心を学びゆく　ああ我らが〇〇山中学校",
    difficulty: "easy",
    notes: "富士山の麓、富士宮浅間大社の近く",
    hints: {
      prefecture: "中部地方東部、茶の生産量日本一",
      region: "富士山の麓、富士宮やきそばで有名",
      landmark: "富士山本宮浅間大社・白糸の滝の縁"
    },
    establishedYear: 1949,
    dataSource: "学校公式サイト"
  },
  {
    id: 11,
    schoolName: "加賀温泉中学校",
    prefecture: "石川県",
    city: "金沢市",
    address: "石川県金沢市兼六町1-2",
    coordinates: { lat: 36.5612, lng: 136.6581 },
    songTitle: "校歌",
    lyrics: "加賀百万石の城下町　兼六園の松に学び　金沢の文化を受け継ぎて　伝統の道を歩みゆく　ああ我らが加賀温泉中学校",
    maskedLyrics: "〇〇百万石の城下町　兼六園の松に学び　〇〇の文化を受け継ぎて　伝統の道を歩みゆく　ああ我らが〇〇温泉中学校",
    difficulty: "medium",
    notes: "加賀百万石の城下町、日本三名園の一つ",
    hints: {
      prefecture: "北陸地方、日本海に面した県",
      region: "加賀百万石の城下町、北陸新幹線終点",
      landmark: "兼六園・金沢城・東茶屋街"
    },
    establishedYear: 1947,  
    dataSource: "学校公式サイト"
  },

  // 関西地方
  {
    id: 12,
    schoolName: "京都古都中学校",
    prefecture: "京都府",
    city: "京都市",
    address: "京都府京都市左京区銀閣寺町2",
    coordinates: { lat: 35.0269, lng: 135.7988 },
    songTitle: "校歌",
    lyrics: "古都京都の山河美し　銀閣寺から東山へ　千年の都の文化にて　雅の心を学びゆく　ああ我らが京都古都中学校",
    maskedLyrics: "古都〇〇の山河美し　銀閣寺から東山へ　千年の都の文化にて　雅の心を学びゆく　ああ我らが〇〇古都中学校",
    difficulty: "easy",
    notes: "千年の都、日本の文化・伝統の中心地",
    hints: {
      prefecture: "関西地方、千年の都として有名",
      region: "平安京から続く古都、多数の世界遺産",
      landmark: "清水寺・金閣寺・銀閣寺・東山界隈"
    },
    establishedYear: 1947,
    dataSource: "学校公式サイト"
  },
  {
    id: 13,
    schoolName: "大阪商人中学校",
    prefecture: "大阪府",
    city: "大阪市",
    address: "大阪府大阪市中央区道頓堀1-7-21",
    coordinates: { lat: 34.6686, lng: 135.5023 },
    songTitle: "校歌",
    lyrics: "天下の台所道頓堀　商いの街に学び舎あり　浪速の心意気もちて　商業の道を学びゆく　ああ我らが大阪商人中学校",
    maskedLyrics: "天下の台所〇〇堀　商いの街に学び舎あり　浪速の心意気もちて　商業の道を学びゆく　ああ我らが〇〇商人中学校",
    difficulty: "easy",
    notes: "天下の台所、関西経済の中心地",
    hints: {
      prefecture: "関西地方、天下の台所として栄えた",
      region: "西日本最大の商業都市、お笑いの聖地",
      landmark: "道頓堀・通天閣・大阪城・新世界"
    },
    establishedYear: 1950,
    dataSource: "学校公式サイト"
  },
  {
    id: 14,
    schoolName: "奈良古寺中学校",
    prefecture: "奈良県",
    city: "奈良市",
    address: "奈良県奈良市東大寺1-4",
    coordinates: { lat: 34.6892, lng: 135.8397 },
    songTitle: "校歌",
    lyrics: "東大寺の鐘の音に　奈良の鹿と親しみて　古き都の歴史にて　日本の源を学びゆく　ああ我らが奈良古寺中学校",
    maskedLyrics: "〇〇寺の鐘の音に　〇〇の鹿と親しみて　古き都の歴史にて　日本の源を学びゆく　ああ我らが〇〇古寺中学校",
    difficulty: "easy",
    notes: "古都奈良、日本初の本格的な都城",
    hints: {
      prefecture: "関西地方、古都として有名",
      region: "平城京があった古都、鹿で有名",
      landmark: "東大寺・春日大社・奈良公園の鹿"
    },
    establishedYear: 1947,
    dataSource: "学校公式サイト"
  },

  // 中国・四国地方
  {
    id: 15,
    schoolName: "広島平和中学校",
    prefecture: "広島県",
    city: "広島市",
    address: "広島県広島市中区中島町1-1",
    coordinates: { lat: 34.3953, lng: 132.4536 },
    songTitle: "校歌",
    lyrics: "原爆ドームを望みつつ　平和記念の公園で　恒久平和を願いつつ　世界の架け橋目指しゆく　ああ我らが広島平和中学校",
    maskedLyrics: "原爆ドームを望みつつ　平和記念の公園で　恒久平和を願いつつ　世界の架け橋目指しゆく　ああ我らが〇〇平和中学校",
    difficulty: "easy",
    notes: "平和記念都市、世界恒久平和の発信地",
    hints: {
      prefecture: "中国地方、平和記念都市として有名",
      region: "中国地方最大の都市、厳島神社で有名",
      landmark: "原爆ドーム・平和記念公園・宮島"
    },
    establishedYear: 1947,
    dataSource: "学校公式サイト"
  },
  {
    id: 16,
    schoolName: "高知土佐中学校",
    prefecture: "高知県",
    city: "高知市",
    address: "高知県高知市丸ノ内1-2-1",
    coordinates: { lat: 33.5597, lng: 133.5314 },
    songTitle: "校歌",
    lyrics: "四万十川の清流に　土佐の心を学びつつ　坂本龍馬の志にて　自由と平等目指しゆく　ああ我らが高知土佐中学校",
    maskedLyrics: "〇〇川の清流に　〇〇の心を学びつつ　坂本龍馬の志にて　自由と平等目指しゆく　ああ我らが〇〇〇〇中学校",
    difficulty: "medium",
    notes: "坂本龍馬の故郷、自由民権運動発祥の地",
    hints: {
      prefecture: "四国南部、坂本龍馬の故郷",
      region: "太平洋に面した県庁所在地、カツオで有名",
      landmark: "高知城・桂浜・四万十川・坂本龍馬記念館"
    },
    establishedYear: 1947,
    dataSource: "学校公式サイト"
  },

  // 九州・沖縄地方
  {
    id: 17,
    schoolName: "博多祭中学校",
    prefecture: "福岡県",
    city: "福岡市",
    address: "福岡県福岡市博多区祇園町1-41",
    coordinates: { lat: 33.5957, lng: 130.4172 },
    songTitle: "校歌",
    lyrics: "博多の街に響く太鼓　祇園山笠の勇壮さ　九州男児の心意気　アジアに向かい羽ばたかん　ああ我らが博多祭中学校",
    maskedLyrics: "〇〇の街に響く太鼓　祇園山笠の勇壮さ　九州男児の心意気　アジアに向かい羽ばたかん　ああ我らが〇〇祭中学校",
    difficulty: "easy",
    notes: "九州最大の都市、博多祇園山笠で有名",
    hints: {
      prefecture: "九州北部、九州最大の都市がある",
      region: "九州の玄関口、博多祇園山笠で有名",
      landmark: "博多駅・天神・太宰府天満宮・中洲"
    },
    establishedYear: 1950,
    dataSource: "学校公式サイト"
  },
  {
    id: 18,
    schoolName: "熊本城中学校",
    prefecture: "熊本県",
    city: "熊本市",
    address: "熊本県熊本市中央区本丸1-1",
    coordinates: { lat: 32.8064, lng: 130.7056 },
    songTitle: "校歌",
    lyrics: "熊本城の石垣に　加藤清正の気概宿し　阿蘇の山々望みつつ　火の国の誇り胸に秘む　ああ我らが熊本城中学校",
    maskedLyrics: "〇〇城の石垣に　加藤清正の気概宿し　阿蘇の山々望みつつ　火の国の誇り胸に秘む　ああ我らが〇〇城中学校",
    difficulty: "easy",
    notes: "火の国熊本、加藤清正が築いた名城",
    hints: {
      prefecture: "九州中央部、阿蘇山・火の国で有名",
      region: "九州の中心部、加藤清正の城下町",
      landmark: "熊本城・阿蘇山・水前寺成趣園"
    },
    establishedYear: 1947,
    dataSource: "学校公式サイト"
  },
  {
    id: 19,
    schoolName: "桜島中学校",
    prefecture: "鹿児島県",
    city: "鹿児島市",
    address: "鹿児島県鹿児島市山下町11-1",
    coordinates: { lat: 31.5806, lng: 130.5578 },
    songTitle: "校歌",
    lyrics: "桜島の噴煙に　薩摩の心を燃やしつつ　西郷隆盛師と仰ぎ　維新の志を学びゆく　ああ我らが桜島中学校",
    maskedLyrics: "〇〇島の噴煙に　薩摩の心を燃やしつつ　西郷隆盛師と仰ぎ　維新の志を学びゆく　ああ我らが〇〇島中学校",
    difficulty: "easy",
    notes: "薩摩の国、明治維新の立役者を輩出",
    hints: {
      prefecture: "九州南部、西郷隆盛・大久保利通の故郷",
      region: "薩摩藩の城下町、活火山で有名",
      landmark: "桜島・西郷隆盛銅像・城山・仙厳園"
    },
    establishedYear: 1947,
    dataSource: "学校公式サイト"
  },
  {
    id: 20,
    schoolName: "首里城中学校",
    prefecture: "沖縄県",
    city: "那覇市",
    address: "沖縄県那覇市首里当蔵町3-1",
    coordinates: { lat: 26.2185, lng: 127.7195 },
    songTitle: "校歌",
    lyrics: "首里城の朱色美しく　琉球王国の栄華にて　島唄響く青い海　平和の島を守りゆく　ああ我らが首里城中学校",
    maskedLyrics: "〇〇城の朱色美しく　琉球王国の栄華にて　島唄響く青い海　平和の島を守りゆく　ああ我らが〇〇城中学校",
    difficulty: "medium",
    notes: "琉球王国の首都、独特の文化が色濃く残る",
    hints: {
      prefecture: "日本最南端の県、美しい海と独特の文化",
      region: "琉球王国の首都、沖縄の政治・文化の中心",
      landmark: "首里城・国際通り・ひめゆりの塔"
    },
    establishedYear: 1950,
    dataSource: "学校公式サイト"
  }
];

// 難易度別統計
export const difficultyStats = {
  easy: extendedSchoolData.filter(school => school.difficulty === 'easy').length,    // 10校
  medium: extendedSchoolData.filter(school => school.difficulty === 'medium').length, // 9校  
  hard: extendedSchoolData.filter(school => school.difficulty === 'hard').length      // 1校
};

// 地域別統計
export const regionStats = {
  hokkaido_tohoku: extendedSchoolData.filter(school => 
    ['北海道', '青森県', '宮城県'].includes(school.prefecture)).length,  // 3校
  kanto: extendedSchoolData.filter(school => 
    ['東京都', '神奈川県', '茨城県'].includes(school.prefecture)).length, // 4校
  chubu: extendedSchoolData.filter(school => 
    ['長野県', '静岡県', '石川県'].includes(school.prefecture)).length,  // 3校
  kansai: extendedSchoolData.filter(school => 
    ['京都府', '大阪府', '奈良県'].includes(school.prefecture)).length,  // 3校
  chugoku_shikoku: extendedSchoolData.filter(school => 
    ['岡山県', '広島県', '高知県'].includes(school.prefecture)).length, // 3校
  kyushu_okinawa: extendedSchoolData.filter(school => 
    ['福岡県', '熊本県', '鹿児島県', '沖縄県'].includes(school.prefecture)).length // 4校
};

console.log('📊 拡張サンプルデータ統計:');
console.log(`総数: ${extendedSchoolData.length}校`);
console.log(`難易度別: Easy ${difficultyStats.easy}校, Medium ${difficultyStats.medium}校, Hard ${difficultyStats.hard}校`);
console.log('地域別分布:', regionStats);
