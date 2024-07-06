const API_URL = 'http://localhost:5000'; // 確保這指向您的Flask後端

let gameState = {
    userName: '',
    anxietySource: '',
    characters: [],
    progress: 0
};

function addDialogueEntry(text, speaker) {
    const dialogueArea = document.getElementById('dialogue-area');
    const entry = document.createElement('div');
    entry.className = `dialogue-entry ${speaker}-dialogue`;
    entry.textContent = text;
    dialogueArea.appendChild(entry);
    dialogueArea.scrollTop = dialogueArea.scrollHeight;
}

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

    await generateCharacters();
    updateScene();
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
                anxietySource: gameState.anxietySource
            }),
        });
        gameState.characters = await response.json();
        addDialogueEntry('角色生成完成！', 'system');
    } catch (error) {
        console.error('Error generating characters:', error);
        addDialogueEntry('生成角色時發生錯誤，使用預設角色。', 'system');
        gameState.characters = [
            { name: "內心的批評者", description: "代表你內心的自我懷疑", help: "挑戰消極想法" },
            { name: "冷靜的智者", description: "一位年長的智者，擁有豐富的人生經驗。", help: "提供理性的建議和長遠的視角。" },
            { name: "活力四射的朋友", description: "一個充滿正能量的年輕人。", help: "通過積極的態度和有趣的活動分散注意力。" },
            { name: "同理心強的諮詢師", description: "專業的心理諮詢師。", help: "提供專業的心理支持和具體的應對策略。" }
        ];
    }
}

function updateScene() {
    document.getElementById('progress').style.width = `${gameState.progress}%`;
    
    addDialogueEntry('你可以選擇與以下角色互動：', 'system');

    const charactersContainer = document.getElementById('characters');
    charactersContainer.innerHTML = '';
    const choicesContainer = document.getElementById('choices');
    choicesContainer.innerHTML = '';

    gameState.characters.forEach(char => {
        const charCard = document.createElement('div');
        charCard.className = 'character-card';
        charCard.innerHTML = `<h3>${char.name}</h3><p>${char.description}</p>`;
        charactersContainer.appendChild(charCard);

        const button = document.createElement('button');
        button.className = 'choice-button';
        button.innerText = `與${char.name}互動`;
        button.onclick = () => interact(char);
        choicesContainer.appendChild(button);
    });
}

async function interact(character) {
    addDialogueEntry(`我選擇與${character.name}互動。`, 'user');

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
                progress: gameState.progress
            }),
        });
        const data = await response.json();
        const lines = data.interaction.split('\n');
        lines.forEach(line => {
            if (line.startsWith(character.name)) {
                addDialogueEntry(line.replace(`${character.name}:`, '').trim(), 'npc');
            } else if (line.startsWith(gameState.userName)) {
                addDialogueEntry(line.replace(`${gameState.userName}:`, '').trim(), 'user');
            }
        });
    } catch (error) {
        console.error('Error generating interaction:', error);
        addDialogueEntry(`${character.name}聆聽了你的煩惱，${character.help}這讓你感到一些釋然。`, 'npc');
    }

    gameState.progress += 10;  // 每次互動增加10%進度
    if (gameState.progress >= 100) {
        endGame();
    } else {
        updateScene();
    }
}

function endGame() {
    addDialogueEntry("恭喜你！通過與不同角色的互動，你已經成功解決了焦慮問題。你學會了新的應對方法，變得更加堅強。", 'system');
    document.getElementById('choices').innerHTML = '<button onclick="location.reload()" class="choice-button">重新開始</button>';
}