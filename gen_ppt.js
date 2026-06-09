const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

// Icon imports
const {
  FaExclamationTriangle, FaMicrophone, FaCalendarAlt, FaTrain,
  FaUsers, FaSyncAlt, FaLightbulb, FaBullseye, FaCar, FaClock,
  FaShieldAlt, FaLock, FaRedo, FaServer, FaDesktop, FaRocket,
  FaUserTie, FaBriefcase, FaChartLine, FaMobileAlt
} = require("react-icons/fa");

function renderIconSvg(IconComponent, color = "#000000", size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

// Color palette - Midnight Executive with gold accent
const C = {
  navy: "0A1628",
  darkNavy: "060F1F",
  midNavy: "152238",
  lightNavy: "1E3352",
  gold: "D4A843",
  lightGold: "E8C96A",
  white: "FFFFFF",
  offWhite: "F0F4F8",
  gray: "8B9BB4",
  lightGray: "CBD5E1",
  accent1: "2E86DE",
  accent2: "10B981",
  accent3: "F59E0B",
  accent4: "EF4444",
  accent5: "8B5CF6",
  accent6: "06B6D4",
};

const makeShadow = () => ({ type: "outer", blur: 8, offset: 3, color: "000000", opacity: 0.25, angle: 135 });
const makeCardShadow = () => ({ type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.2, angle: 135 });

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "VoiCal Team";
  pres.title = "VoiCal - AI语音智能日历助手 产品介绍";

  // Pre-render icons
  const icons = {};
  const iconMap = {
    mic: [FaMicrophone, C.gold],
    cal: [FaCalendarAlt, C.gold],
    train: [FaTrain, C.gold],
    users: [FaUsers, C.gold],
    sync: [FaSyncAlt, C.gold],
    bulb: [FaLightbulb, C.gold],
    warn: [FaExclamationTriangle, C.accent4],
    target: [FaBullseye, C.gold],
    car: [FaCar, C.white],
    clock: [FaClock, C.white],
    shield: [FaShieldAlt, C.gold],
    lock: [FaLock, C.gold],
    redo: [FaRedo, C.gold],
    server: [FaServer, C.gold],
    desktop: [FaDesktop, C.gold],
    rocket: [FaRocket, C.gold],
    userTie: [FaUserTie, C.gold],
    brief: [FaBriefcase, C.gold],
    chart: [FaChartLine, C.gold],
    mobile: [FaMobileAlt, C.gold],
    micW: [FaMicrophone, C.white],
    calW: [FaCalendarAlt, C.white],
    trainW: [FaTrain, C.white],
    usersW: [FaUsers, C.white],
    syncW: [FaSyncAlt, C.white],
    bulbW: [FaLightbulb, C.white],
  };

  for (const [key, [comp, color]] of Object.entries(iconMap)) {
    icons[key] = await iconToBase64Png(comp, "#" + color);
  }

  // ═══════════════════════════════════════════════════════════
  // SLIDE 1 — Cover
  // ═══════════════════════════════════════════════════════════
  let slide = pres.addSlide();
  slide.background = { color: C.darkNavy };

  // Decorative circles
  slide.addShape(pres.shapes.OVAL, { x: -1.5, y: -1.5, w: 4, h: 4, fill: { color: C.gold, transparency: 92 } });
  slide.addShape(pres.shapes.OVAL, { x: 7.5, y: 3.5, w: 5, h: 5, fill: { color: C.gold, transparency: 92 } });

  // Gold accent line
  slide.addShape(pres.shapes.RECTANGLE, { x: 3.5, y: 1.6, w: 3, h: 0.04, fill: { color: C.gold } });

  // Title
  slide.addText("VoiCal", {
    x: 0.5, y: 1.8, w: 9, h: 1.2,
    fontSize: 54, fontFace: "Arial Black", color: C.white,
    align: "center", bold: true, margin: 0
  });
  slide.addText("AI 语音智能日历助手", {
    x: 0.5, y: 2.85, w: 9, h: 0.7,
    fontSize: 28, fontFace: "Arial", color: C.gold,
    align: "center", margin: 0
  });

  // Gold accent line below
  slide.addShape(pres.shapes.RECTANGLE, { x: 3.5, y: 3.65, w: 3, h: 0.04, fill: { color: C.gold } });

  // Slogan
  slide.addText("让每一句话都变成日程，让每一次出行都有规划", {
    x: 0.5, y: 3.9, w: 9, h: 0.6,
    fontSize: 16, fontFace: "Arial", color: C.gray,
    align: "center", italic: true, margin: 0
  });

  // Mic icon
  slide.addImage({ data: icons.mic, x: 4.55, y: 4.6, w: 0.9, h: 0.9 });

  // ═══════════════════════════════════════════════════════════
  // SLIDE 2 — Pain Points
  // ═══════════════════════════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  // Title bar
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy } });
  slide.addText("行业痛点分析", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.white, margin: 0
  });

  const painPoints = [
    { title: "操作成本高", desc: "传统日历需要 4 步操作才能创建一个日程", color: C.accent4 },
    { title: "信息孤岛严重", desc: "日历、地图、12306、会议 App 各自独立", color: C.accent3 },
    { title: "被动记录", desc: "不会检测冲突、推荐时段、规划路线", color: C.accent5 },
    { title: "提醒单一", desc: "静音弹窗通知容易被忽略", color: C.accent1 },
    { title: "多平台割裂", desc: "钉钉、企微、Google Calendar 日程数据分散", color: C.accent6 },
  ];

  painPoints.forEach((p, i) => {
    const y = 1.3 + i * 0.82;
    // Card background
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: y, w: 8.8, h: 0.7,
      fill: { color: C.white }, shadow: makeCardShadow()
    });
    // Left accent
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: y, w: 0.08, h: 0.7, fill: { color: p.color }
    });
    // Number circle
    slide.addShape(pres.shapes.OVAL, {
      x: 0.85, y: y + 0.1, w: 0.5, h: 0.5, fill: { color: p.color }
    });
    slide.addText(String(i + 1), {
      x: 0.85, y: y + 0.1, w: 0.5, h: 0.5,
      fontSize: 16, fontFace: "Arial", color: C.white,
      align: "center", valign: "middle", bold: true, margin: 0
    });
    // Title
    slide.addText(p.title, {
      x: 1.55, y: y + 0.05, w: 2.2, h: 0.6,
      fontSize: 15, fontFace: "Arial", color: C.navy, bold: true, valign: "middle", margin: 0
    });
    // Description
    slide.addText(p.desc, {
      x: 3.8, y: y + 0.05, w: 5.4, h: 0.6,
      fontSize: 13, fontFace: "Arial", color: "475569", valign: "middle", margin: 0
    });
  });

  // ═══════════════════════════════════════════════════════════
  // SLIDE 3 — User Scenarios
  // ═══════════════════════════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy } });
  slide.addText("用户场景分析", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.white, margin: 0
  });

  const scenarios = [
    { scene: "开车途中安排会议", pain: "无法安全操作手机", solution: "语音指令创建会议 + 自动生成视频链接" },
    { scene: "出差前查高铁", pain: "需切换地图+12306+日历", solution: "语音一句话完成查车次→创建出行日程" },
    { scene: "多会议时间冲突", pain: "手动逐个调整耗时", solution: "AI 自动分析优先级，推荐空闲时段" },
    { scene: "跨平台日程不一致", pain: "手动同步多平台", solution: "一键同步钉钉/企微/Google/Outlook" },
    { scene: "会议结束跟进", pain: "手动记录纪要很麻烦", solution: "AI 自动生成结构化纪要 + Action Items" },
  ];

  // Table header
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.25, w: 8.8, h: 0.5, fill: { color: C.navy } });
  slide.addText("场景", { x: 0.7, y: 1.25, w: 2.3, h: 0.5, fontSize: 13, fontFace: "Arial", color: C.gold, bold: true, valign: "middle", margin: 0 });
  slide.addText("痛点", { x: 3.05, y: 1.25, w: 2.5, h: 0.5, fontSize: 13, fontFace: "Arial", color: C.gold, bold: true, valign: "middle", margin: 0 });
  slide.addText("VoiCal 解决方案", { x: 5.6, y: 1.25, w: 3.7, h: 0.5, fontSize: 13, fontFace: "Arial", color: C.gold, bold: true, valign: "middle", margin: 0 });

  scenarios.forEach((s, i) => {
    const y = 1.8 + i * 0.7;
    const bgColor = i % 2 === 0 ? C.white : "EDF2F7";
    slide.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: y, w: 8.8, h: 0.65, fill: { color: bgColor } });
    slide.addText(s.scene, { x: 0.7, y: y, w: 2.3, h: 0.65, fontSize: 12, fontFace: "Arial", color: C.navy, bold: true, valign: "middle", margin: 0 });
    slide.addText(s.pain, { x: 3.05, y: y, w: 2.5, h: 0.65, fontSize: 12, fontFace: "Arial", color: C.accent4, valign: "middle", margin: 0 });
    slide.addText(s.solution, { x: 5.6, y: y, w: 3.7, h: 0.65, fontSize: 12, fontFace: "Arial", color: C.accent2, bold: true, valign: "middle", margin: 0 });
  });

  // ═══════════════════════════════════════════════════════════
  // SLIDE 4 — Target Users
  // ═══════════════════════════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy } });
  slide.addText("目标人群定位", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.white, margin: 0
  });

  // Core users - left card
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 5.5, h: 3.8,
    fill: { color: C.white }, shadow: makeShadow()
  });
  // Card header
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.3, w: 5.5, h: 0.6, fill: { color: C.navy } });
  slide.addImage({ data: icons.userTie, x: 0.7, y: 1.35, w: 0.45, h: 0.45 });
  slide.addText("核心用户：中高层商务人士", {
    x: 1.25, y: 1.3, w: 4.5, h: 0.6,
    fontSize: 16, fontFace: "Arial", color: C.gold, bold: true, valign: "middle", margin: 0
  });

  const coreDetails = [
    { label: "职业", value: "企业高管、项目经理、销售总监、创业者" },
    { label: "日程密度", value: "每日 5-15 个日程，涉及内外部会议、客户拜访、差旅" },
    { label: "工具习惯", value: "同时使用钉钉/企微 + Google Calendar/Outlook" },
    { label: "核心诉求", value: "省时间、少出错、不漏事" },
  ];

  coreDetails.forEach((d, i) => {
    const y = 2.1 + i * 0.7;
    slide.addShape(pres.shapes.OVAL, { x: 0.8, y: y + 0.1, w: 0.35, h: 0.35, fill: { color: C.gold } });
    slide.addText(d.label, {
      x: 0.75, y: y + 0.08, w: 0.45, h: 0.4,
      fontSize: 9, fontFace: "Arial", color: C.navy, align: "center", valign: "middle", bold: true, margin: 0
    });
    slide.addText(d.value, {
      x: 1.35, y: y, w: 4.4, h: 0.6,
      fontSize: 12, fontFace: "Arial", color: "475569", valign: "middle", margin: 0
    });
  });

  // Expanded users - right cards
  const expandUsers = [
    { title: "自由职业者", desc: "管理多个客户项目的交付时间线", iconKey: "brief" },
    { title: "行政 / 秘书", desc: "为领导协调日程、安排会议室", iconKey: "cal" },
    { title: "个人用户", desc: "语音快速管理日常生活安排", iconKey: "mobile" },
  ];

  slide.addShape(pres.shapes.RECTANGLE, { x: 6.3, y: 1.3, w: 3.3, h: 0.6, fill: { color: C.lightNavy } });
  slide.addText("扩展用户", {
    x: 6.3, y: 1.3, w: 3.3, h: 0.6,
    fontSize: 16, fontFace: "Arial", color: C.white, bold: true, align: "center", valign: "middle", margin: 0
  });

  expandUsers.forEach((u, i) => {
    const y = 2.05 + i * 1.15;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 6.3, y: y, w: 3.3, h: 1.0,
      fill: { color: C.white }, shadow: makeCardShadow()
    });
    slide.addImage({ data: icons[u.iconKey], x: 6.5, y: y + 0.2, w: 0.45, h: 0.45 });
    slide.addText(u.title, {
      x: 7.1, y: y + 0.08, w: 2.3, h: 0.4,
      fontSize: 13, fontFace: "Arial", color: C.navy, bold: true, valign: "middle", margin: 0
    });
    slide.addText(u.desc, {
      x: 7.1, y: y + 0.5, w: 2.3, h: 0.4,
      fontSize: 11, fontFace: "Arial", color: "64748B", valign: "top", margin: 0
    });
  });

  // ═══════════════════════════════════════════════════════════
  // SLIDE 5 — Competitive Comparison
  // ═══════════════════════════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy } });
  slide.addText("产品核心差异", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.white, margin: 0
  });

  // Table
  const compHeaders = ["对比维度", "传统日历 App", "VoiCal"];
  const compRows = [
    ["交互方式", "手动点击输入", "语音自然语言交互"],
    ["智能程度", "被动记录", "AI Agent 主动规划编排执行"],
    ["功能边界", "仅日程 CRUD", "日程+出行+会议+任务 一体化"],
    ["冲突处理", "提示冲突", "AI 自动分析+推荐解决方案"],
    ["出行规划", "需切换地图/12306", "日历内直接查高铁+创建出行日程"],
    ["多平台", "单平台日历", "钉钉/企微/Google/Outlook 双向同步"],
  ];

  // Header row
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.25, w: 8.8, h: 0.55, fill: { color: C.navy } });
  slide.addText(compHeaders[0], { x: 0.7, y: 1.25, w: 2.0, h: 0.55, fontSize: 13, fontFace: "Arial", color: C.gold, bold: true, valign: "middle", margin: 0 });
  slide.addText(compHeaders[1], { x: 2.75, y: 1.25, w: 3.0, h: 0.55, fontSize: 13, fontFace: "Arial", color: C.lightGray, bold: true, valign: "middle", margin: 0 });
  slide.addText(compHeaders[2], { x: 5.8, y: 1.25, w: 3.5, h: 0.55, fontSize: 13, fontFace: "Arial", color: C.gold, bold: true, valign: "middle", margin: 0 });

  compRows.forEach((row, i) => {
    const y = 1.85 + i * 0.6;
    const bgColor = i % 2 === 0 ? C.white : "EDF2F7";
    slide.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: y, w: 8.8, h: 0.55, fill: { color: bgColor } });
    slide.addText(row[0], { x: 0.7, y: y, w: 2.0, h: 0.55, fontSize: 12, fontFace: "Arial", color: C.navy, bold: true, valign: "middle", margin: 0 });
    slide.addText(row[1], { x: 2.75, y: y, w: 3.0, h: 0.55, fontSize: 12, fontFace: "Arial", color: "94A3B8", valign: "middle", margin: 0 });
    slide.addText(row[2], { x: 5.8, y: y, w: 3.5, h: 0.55, fontSize: 12, fontFace: "Arial", color: C.accent2, bold: true, valign: "middle", margin: 0 });
  });

  // ═══════════════════════════════════════════════════════════
  // SLIDE 6 — Core Features
  // ═══════════════════════════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy } });
  slide.addText("核心功能模块", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.white, margin: 0
  });

  const features = [
    { title: "语音交互", desc: "Push-to-Talk、实时声波可视化\nAgent处理日志、Barge-in打断", icon: "micW", bg: C.accent1 },
    { title: "日程管理", desc: "语音创建日程、冲突检测\nAI智能重排、优先级管理", icon: "calW", bg: C.accent2 },
    { title: "出行规划", desc: "多模式路线对比、跨城检测\n12306实时查票、高铁日程联动", icon: "trainW", bg: C.accent3 },
    { title: "会议协作", desc: "一键创建会议+视频链接\n多平台支持、AI会议纪要", icon: "usersW", bg: C.accent5 },
    { title: "多端同步", desc: "钉钉/企微/Google/Outlook\n双向实时同步", icon: "syncW", bg: C.accent6 },
    { title: "智能建议", desc: "交通方式卡片、冲突预警\n时间推荐、快捷指令", icon: "bulbW", bg: C.gold },
  ];

  features.forEach((f, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.5 + col * 3.1;
    const y = 1.2 + row * 2.15;

    // Card
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 2.9, h: 1.95,
      fill: { color: C.white }, shadow: makeCardShadow()
    });
    // Icon circle
    slide.addShape(pres.shapes.OVAL, {
      x: x + 0.2, y: y + 0.2, w: 0.6, h: 0.6, fill: { color: f.bg }
    });
    slide.addImage({ data: icons[f.icon], x: x + 0.3, y: y + 0.3, w: 0.4, h: 0.4 });
    // Title
    slide.addText(f.title, {
      x: x + 0.95, y: y + 0.2, w: 1.7, h: 0.6,
      fontSize: 15, fontFace: "Arial", color: C.navy, bold: true, valign: "middle", margin: 0
    });
    // Description
    slide.addText(f.desc, {
      x: x + 0.2, y: y + 0.95, w: 2.5, h: 0.85,
      fontSize: 11, fontFace: "Arial", color: "64748B", valign: "top", margin: 0
    });
  });

  // ═══════════════════════════════════════════════════════════
  // SLIDE 7 — Business Flow
  // ═══════════════════════════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: C.navy };

  slide.addText("业务流程图", {
    x: 0.6, y: 0.2, w: 8, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.white, margin: 0
  });

  const flowSteps = [
    { label: "用户语音\n输入", color: C.accent1 },
    { label: "ASR\n语音识别", color: C.accent6 },
    { label: "NLU\n意图理解", color: C.accent5 },
    { label: "Agent\n编排任务", color: C.accent2 },
    { label: "工具执行", color: C.accent3 },
    { label: "LLM摘要\n+TTS播报", color: C.gold },
  ];

  const flowY = 1.5;
  const stepW = 1.25;
  const gap = 0.3;
  const startX = (10 - (flowSteps.length * stepW + (flowSteps.length - 1) * gap)) / 2;

  flowSteps.forEach((s, i) => {
    const x = startX + i * (stepW + gap);
    // Box
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x, y: flowY, w: stepW, h: 1.1,
      fill: { color: s.color }, shadow: makeShadow()
    });
    slide.addText(s.label, {
      x: x, y: flowY, w: stepW, h: 1.1,
      fontSize: 12, fontFace: "Arial", color: C.white,
      align: "center", valign: "middle", bold: true, margin: 0
    });
    // Arrow
    if (i < flowSteps.length - 1) {
      const arrowX = x + stepW + 0.02;
      slide.addText("▶", {
        x: arrowX, y: flowY + 0.3, w: gap - 0.04, h: 0.5,
        fontSize: 14, fontFace: "Arial", color: C.gold,
        align: "center", valign: "middle", margin: 0
      });
    }
  });

  // Detail boxes below
  slide.addText("工具执行层详情", {
    x: 0.6, y: 3.0, w: 8, h: 0.5,
    fontSize: 16, fontFace: "Arial", color: C.gold, bold: true, margin: 0
  });

  const tools = [
    { name: "高德地图", desc: "路线规划、地理编码", color: C.accent1 },
    { name: "12306", desc: "高铁查询、余票检索", color: C.accent6 },
    { name: "日程管理", desc: "CRUD、冲突检测、智能重排", color: C.accent2 },
    { name: "会议协作", desc: "创建会议、视频链接、邀约", color: C.accent5 },
  ];

  tools.forEach((t, i) => {
    const x = 0.6 + i * 2.3;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 3.55, w: 2.1, h: 1.5,
      fill: { color: C.midNavy }, shadow: makeCardShadow()
    });
    slide.addShape(pres.shapes.RECTANGLE, { x: x, y: 3.55, w: 2.1, h: 0.06, fill: { color: t.color } });
    slide.addText(t.name, {
      x: x + 0.15, y: 3.7, w: 1.8, h: 0.45,
      fontSize: 14, fontFace: "Arial", color: C.white, bold: true, margin: 0
    });
    slide.addText(t.desc, {
      x: x + 0.15, y: 4.15, w: 1.8, h: 0.75,
      fontSize: 11, fontFace: "Arial", color: C.gray, margin: 0
    });
  });

  // ═══════════════════════════════════════════════════════════
  // SLIDE 8 — Technical Architecture
  // ═══════════════════════════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: C.navy };

  slide.addText("产品技术架构", {
    x: 0.6, y: 0.2, w: 8, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.white, margin: 0
  });

  slide.addText("五层架构设计", {
    x: 0.6, y: 0.8, w: 8, h: 0.4,
    fontSize: 14, fontFace: "Arial", color: C.gold, italic: true, margin: 0
  });

  const layers = [
    { id: "L5", name: "输出聚合层", desc: "LLM 摘要 + 讯飞 TTS 语音合成播报", color: C.gold },
    { id: "L4", name: "工具执行层", desc: "高德路线 / 12306高铁 / 日程管理 / 会议协作", color: C.accent2 },
    { id: "L3", name: "Agent 编排层", desc: "多步任务规划 + DAG 执行计划 + 工具调度", color: C.accent5 },
    { id: "L2", name: "NLU 理解层", desc: "智谱 GLM-4 意图识别 + 槽位抽取", color: C.accent1 },
    { id: "L1", name: "ASR 识别层", desc: "科大讯飞 WebSocket 实时语音识别", color: C.accent6 },
    { id: "L0", name: "语音采集层", desc: "麦克风录音 + VAD 能量检测", color: C.accent3 },
  ];

  layers.forEach((l, i) => {
    const y = 1.25 + i * 0.7;
    // Layer bar
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: y, w: 8.8, h: 0.6,
      fill: { color: C.midNavy }, shadow: makeCardShadow()
    });
    // Left accent
    slide.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: y, w: 0.08, h: 0.6, fill: { color: l.color } });
    // Layer ID badge
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.85, y: y + 0.1, w: 0.6, h: 0.4, fill: { color: l.color }
    });
    slide.addText(l.id, {
      x: 0.85, y: y + 0.1, w: 0.6, h: 0.4,
      fontSize: 12, fontFace: "Consolas", color: C.white,
      align: "center", valign: "middle", bold: true, margin: 0
    });
    // Name
    slide.addText(l.name, {
      x: 1.65, y: y, w: 2.2, h: 0.6,
      fontSize: 14, fontFace: "Arial", color: C.white, bold: true, valign: "middle", margin: 0
    });
    // Description
    slide.addText(l.desc, {
      x: 3.9, y: y, w: 5.3, h: 0.6,
      fontSize: 12, fontFace: "Arial", color: C.gray, valign: "middle", margin: 0
    });
  });

  // ═══════════════════════════════════════════════════════════
  // SLIDE 9 — Tech Stack
  // ═══════════════════════════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy } });
  slide.addText("技术栈总览", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.white, margin: 0
  });

  const techItems = [
    { cat: "前端", tech: "Vue 3 + Vite + Socket.IO Client", color: C.accent2 },
    { cat: "后端", tech: "Flask + Flask-SocketIO + FastAPI", color: C.accent1 },
    { cat: "AI 大模型", tech: "智谱 GLM-4 (ZhipuAI SDK)", color: C.accent5 },
    { cat: "语音识别", tech: "科大讯飞 WebSocket 实时语音听写", color: C.accent6 },
    { cat: "语音合成", tech: "科大讯飞 WebSocket 语音合成", color: C.accent6 },
    { cat: "数据库", tech: "PostgreSQL 16 (生产) / SQLite (开发)", color: C.accent3 },
    { cat: "地图服务", tech: "高德地图 REST API", color: C.accent2 },
    { cat: "高铁查询", tech: "12306 官方 API", color: C.accent1 },
    { cat: "实时通信", tech: "WebSocket (Socket.IO)", color: C.accent5 },
    { cat: "容器化", tech: "Docker + Docker Compose", color: C.accent4 },
  ];

  techItems.forEach((t, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 4.7;
    const y = 1.2 + row * 0.82;

    slide.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 4.5, h: 0.7,
      fill: { color: C.white }, shadow: makeCardShadow()
    });
    slide.addShape(pres.shapes.RECTANGLE, { x: x, y: y, w: 0.06, h: 0.7, fill: { color: t.color } });
    slide.addText(t.cat, {
      x: x + 0.2, y: y, w: 1.2, h: 0.7,
      fontSize: 12, fontFace: "Arial", color: C.navy, bold: true, valign: "middle", margin: 0
    });
    slide.addText(t.tech, {
      x: x + 1.4, y: y, w: 2.9, h: 0.7,
      fontSize: 11, fontFace: "Arial", color: "475569", valign: "middle", margin: 0
    });
  });

  // ═══════════════════════════════════════════════════════════
  // SLIDE 10 — Security
  // ═══════════════════════════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: C.navy };

  slide.addText("安全与容错机制", {
    x: 0.6, y: 0.2, w: 8, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.white, margin: 0
  });

  const secItems = [
    { title: "JWT 认证 + RBAC", desc: "basic / admin / pro 三级权限控制，细粒度访问管理", color: C.accent1 },
    { title: "AES-256 字段加密", desc: "手机号、邮箱、Token 等敏感信息加密存储", color: C.accent2 },
    { title: "写操作确认", desc: "TTS 播报确认，10秒超时自动取消，防止误操作", color: C.accent3 },
    { title: "超时熔断 + 指数退避重试", desc: "工具并行执行，单个超时不影响整体，自动重试", color: C.accent5 },
    { title: "TTS 双引擎容灾", desc: "讯飞主引擎故障时自动切换阿里云备用引擎", color: C.accent6 },
    { title: "离线消息兆底", desc: "网络中断时写入 Redis 队列，恢复后自动执行", color: C.accent4 },
  ];

  secItems.forEach((s, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 4.7;
    const y = 1.2 + row * 1.4;

    slide.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 4.5, h: 1.2,
      fill: { color: C.midNavy }, shadow: makeCardShadow()
    });
    slide.addShape(pres.shapes.RECTANGLE, { x: x, y: y, w: 4.5, h: 0.06, fill: { color: s.color } });
    slide.addText(s.title, {
      x: x + 0.2, y: y + 0.15, w: 4.1, h: 0.4,
      fontSize: 14, fontFace: "Arial", color: C.white, bold: true, margin: 0
    });
    slide.addText(s.desc, {
      x: x + 0.2, y: y + 0.6, w: 4.1, h: 0.5,
      fontSize: 11, fontFace: "Arial", color: C.gray, margin: 0
    });
  });

  // ═══════════════════════════════════════════════════════════
  // SLIDE 11 — Frontend Experience
  // ═══════════════════════════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: C.offWhite };

  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy } });
  slide.addText("前端体验设计", {
    x: 0.6, y: 0.15, w: 8, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.white, margin: 0
  });

  const uxFeatures = [
    { title: "深夜指挥室风格", desc: "极深海军蓝 + 金色点缀，专为商务决策者设计的高端视觉体验", color: C.gold },
    { title: "三视图切换", desc: "日 / 周 / 月视图自由切换，AI 新建事件呼吸光晕效果，视觉反馈清晰", color: C.accent1 },
    { title: "响应式适配", desc: "桌面三栏 → 平板两栏 → 手机单列，无缝覆盖全终端场景", color: C.accent2 },
    { title: "移动端优化", desc: "底部 Tab 导航 + 语音悬浮按钮 (VoiceFAB) + 全屏语音界面", color: C.accent5 },
  ];

  uxFeatures.forEach((f, i) => {
    const y = 1.2 + i * 1.05;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 9, h: 0.9,
      fill: { color: C.white }, shadow: makeCardShadow()
    });
    slide.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: y, w: 0.08, h: 0.9, fill: { color: f.color } });
    slide.addText(f.title, {
      x: 0.8, y: y + 0.05, w: 2.5, h: 0.8,
      fontSize: 15, fontFace: "Arial", color: C.navy, bold: true, valign: "middle", margin: 0
    });
    slide.addText(f.desc, {
      x: 3.3, y: y + 0.05, w: 6.0, h: 0.8,
      fontSize: 12, fontFace: "Arial", color: "475569", valign: "middle", margin: 0
    });
  });

  // ═══════════════════════════════════════════════════════════
  // SLIDE 12 — Vision
  // ═══════════════════════════════════════════════════════════
  slide = pres.addSlide();
  slide.background = { color: C.darkNavy };

  // Decorative circles
  slide.addShape(pres.shapes.OVAL, { x: -1, y: -1, w: 3.5, h: 3.5, fill: { color: C.gold, transparency: 93 } });
  slide.addShape(pres.shapes.OVAL, { x: 7, y: 3, w: 5, h: 5, fill: { color: C.gold, transparency: 93 } });

  slide.addText("产品愿景", {
    x: 0.5, y: 0.8, w: 9, h: 0.7,
    fontSize: 32, fontFace: "Arial Black", color: C.gold,
    align: "center", margin: 0
  });

  // Gold line
  slide.addShape(pres.shapes.RECTANGLE, { x: 4, y: 1.6, w: 2, h: 0.04, fill: { color: C.gold } });

  slide.addText("成为商务人士的", {
    x: 0.5, y: 1.9, w: 9, h: 0.6,
    fontSize: 20, fontFace: "Arial", color: C.white,
    align: "center", margin: 0
  });
  slide.addText([
    { text: "\"AI 时间管理伙伴\"", options: { fontSize: 36, fontFace: "Arial Black", color: C.gold, bold: true } }
  ], {
    x: 0.5, y: 2.4, w: 9, h: 0.8, align: "center", margin: 0
  });

  // Vision pillars
  const pillars = [
    { text: "理解意图", color: C.accent1 },
    { text: "规划路径", color: C.accent2 },
    { text: "执行任务", color: C.accent5 },
    { text: "主动提醒", color: C.accent3 },
  ];

  pillars.forEach((p, i) => {
    const x = 1.2 + i * 2.1;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 3.5, w: 1.8, h: 0.7,
      fill: { color: p.color }, shadow: makeShadow()
    });
    slide.addText(p.text, {
      x: x, y: 3.5, w: 1.8, h: 0.7,
      fontSize: 16, fontFace: "Arial", color: C.white,
      align: "center", valign: "middle", bold: true, margin: 0
    });
  });

  slide.addText("不只是一个记录工具，而是能理解意图、规划路径、执行任务、主动提醒的智能助手", {
    x: 0.5, y: 4.5, w: 9, h: 0.6,
    fontSize: 14, fontFace: "Arial", color: C.gray,
    align: "center", italic: true, margin: 0
  });

  // Rocket icon
  slide.addImage({ data: icons.rocket, x: 4.55, y: 5.0, w: 0.6, h: 0.6 });

  // Write file
  await pres.writeFile({ fileName: "D:\\JAVA\\voice\\VoiCal产品介绍.pptx" });
  console.log("PPT generated successfully!");
}

main().catch(console.error);
