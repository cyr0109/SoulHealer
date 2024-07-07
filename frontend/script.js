const API_URL = 'http://localhost:5000'; // 確保這指向您的Flask後端

let gameState = {
    userName: '',
    anxietySource: '',
    story: '',
    characters: [],
    userThought: '',
    selectedCharacters: null,
    progress: 0
};


async function startGame() {
    gameState.userName = document.getElementById('user-name').value;
    gameState.anxietySource = document.getElementById('anxiety-source').value;
    
    if (!gameState.userName || !gameState.anxietySource) {
        alert('請填寫您的名字和焦慮來源');
        return;
    }

    document.getElementById('user-input').style.display = 'none';
    document.getElementById('game-play').style.display = 'block';

    addDialogueEntry(`歡迎，${gameState.userName}！讓我們開始解決你的焦慮問題。`, 'system');
    addDialogueEntry(`我的焦慮來源是：${gameState.anxietySource}`, 'user');

    await generateStory();
    await generateCharacters();
    createCharacters();
}

async function generateStory() {
    addDialogueEntry('正在生成適合你的故事...', 'system');
    try {
        const response = await fetch(`${API_URL}/generate-story`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userName: gameState.userName,
                anxietySource: gameState.anxietySource
            }),
        });
        const data = await response.json();
        gameState.story = data.story;
        addDialogueEntry('故事生成完成！', 'system');
        addDialogueEntry(gameState.story, 'system');
    } catch (error) {
        console.error('Error generating characters:', error);
        addDialogueEntry('生成角色時發生錯誤，使用預設故事。', 'system');
        gameState.story = '有個人叫小菜，然後他就被端走了';
    }
}

async function generateCharacters() {
    addDialogueEntry('正在生成適合你的角色...', 'system');
    try {
        const response = await fetch(`${API_URL}/generate-characters`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userName: gameState.userName,
                anxietySource: gameState.anxietySource,
                story: gameState.story
            }),
        });
        gameState.characters = await response.json();
        addDialogueEntry('角色生成完成！', 'system');
    } catch (error) {
        console.error('Error generating characters:', error);
        addDialogueEntry('生成角色時發生錯誤，使用預設角色。', 'system');
        gameState.characters = [
            {"name": "內心的批評者", "description": "代表你內心的自我懷疑", "help": "挑戰消極想法"},
            {"name": "冷靜的智者", "description": "一位年長的智者，擁有豐富的人生經驗。", "help": "提供理性的建議和長遠的視角。"},
            {"name": "活力四射的朋友", "description": "一個充滿正能量的年輕人。", "help": "通過積極的態度和有趣的活動分散注意力。"},
            {"name": "同理心強的諮詢師", "description": "專業的心理諮詢師。", "help": "提供專業的心理支持和具體的應對策略。"},
            {"name": "勇敢的冒險家", "description": "一位無所畏懼的冒險家，鼓勵你面對恐懼。", "help": "通過設定挑戰來幫助你建立自信和韌性。"},
            {"name": "樂觀的激勵者", "description": "一位帶來希望和積極心態的激勵者。", "help": "通過分享正面經歷和鼓勵正向思維來幫助你保持積極心態。"}
        ];
    }
}


async function interact(character) {
    // addDialogueEntry(`${character.name}正在生成回應你的話...`, 'system');
    gameState.userThought = document.getElementById('user-thought').value;
    addDialogueEntry(`${gameState.userThought}`, 'user');
    document.getElementById('user-thought').value = '';
    try {
        const response = await fetch(`${API_URL}/generate-interaction`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userName: gameState.userName,
                anxietySource: gameState.anxietySource,
                character: character,
                userThought: gameState.userThought,
                progress: gameState.progress
            }),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        // 處理接收到的互動數據
        processInteraction(data.interaction);
    } catch (error) {
        console.error('Error generating interaction:', error);
        // 處理錯誤情況
    }
}

function processInteraction(interactionData) {
    console.log("Received interaction data:", interactionData);  // 添加日志

    // 将交互数据按行分割
    // const lines = interactionData.split('\n');
    // let userFeelingsChange = '';

    // console.log("Number of lines:", lines.length);  // 添加日志

    // 遍历每一行
    // lines.forEach((line, index) => {
    //     console.log(`Processing line ${index}:`, line);  // 添加日志
    //     line = line.trim();
    //     if (line) {
    //         if (line.toLowerCase().startsWith('用户的感受变化:')) {
    //             // 存储用户感受变化
    //             userFeelingsChange = line.substring(line.indexOf(':') + 1).trim();
    //         } else if (line.includes(':')) {
    //             // 处理对话行
    //             const [speaker, text] = line.split(':').map(part => part.trim());
    //             if (speaker === gameState.userName) {
    //                 // 用户对话
    //                 addDialogueEntry(text, 'user');
    //             } else {
    //                 // 角色对话
    //                 addDialogueEntry(text, 'npc');
    //             }
    //         } else {
    //             // 处理不符合预期格式的行
    //             console.log("Unexpected line format:", line);
    //             addDialogueEntry(line, 'system');
    //         }
    //     }
    // });
    addDialogueEntry(interactionData, 'npc');
    // 添加用户感受变化的描述
    // if (userFeelingsChange) {
    //     addDialogueEntry(userFeelingsChange, 'npc');
    // }

    // 更新游戏进度
    gameState.progress += 10;
    updateProgressBar();

    // 检查是否游戏结束
    if (gameState.progress >= 100) {
        endGame();
    } else {
        updateScene();
    }
}

function addDialogueEntry(text, speaker) {
    console.log(`Adding dialogue entry - Speaker: ${speaker}, Text: ${text}`);  // 添加日志
    const dialogueArea = document.getElementById('dialogue-area');
    const entry = document.createElement('div');
    entry.className = `dialogue-entry ${speaker}-dialogue`;
    entry.textContent = text;
    dialogueArea.appendChild(entry);
    dialogueArea.scrollTop = dialogueArea.scrollHeight;
}

function updateProgressBar() {
    const progressBar = document.getElementById('progress');
    progressBar.style.width = `${gameState.progress}%`;
}

function endGame() {
    addDialogueEntry("恭喜你！通过与不同角色的互动，你已经成功解决了焦虑问题。你学会了新的应对方法，变得更加坚强。", 'system');
    const choicesContainer = document.getElementById('choices');
    choicesContainer.innerHTML = '<button onclick="location.reload()" class="choice-button">重新开始</button>';
}

function updateScene() {
    // 清空之前的选择
    // const choicesContainer = document.getElementById('choices');
    // choicesContainer.innerHTML = '';

    // 为每个角色创建一个新的选择按钮
    gameState.characters.forEach(char => {
        const button = document.createElement('button');
        button.className = 'choice-button';
        button.innerText = `與${char.name}互動`;
        button.onclick = () => interact(char);
        choicesContainer.appendChild(button);
    });
}
function createCharacters() {
    const choicesContainer = document.getElementById('choices');
    gameState.characters.forEach(char => {
        const button = document.createElement('button');
        button.className = 'choice-button';
        // button.innerText = `與${char.name}互動`;
        button.innerHTML = `
            <h3>${char.name}</h3>
            <p>${char.description}</p>
            <p>${char.help}</p>
        `;
        // button.onclick = () => interact(char);
        button.onclick = () => selectedCharacters = char;
        choicesContainer.appendChild(button);
    });
}

function enterThought() {
    interact(selectedCharacters);
}