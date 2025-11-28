function initBackgrounds() {
    // 渲染背景选择
    let backgrounds_div = $("#backgrounds_div");
    backgrounds_div.empty();
    for (const [key, value] of Object.entries(backgrounds)) {
        let bg_html = `
        <div class="col-3">
            <label class="form-imagecheck mb-2">
                <input name="background" type="radio" value="${key}" class="form-imagecheck-input" onchange="updateCanvas()"${key=="c15" ? " checked" : ""}/>
                <span class="form-imagecheck-figure">
                    <img class="form-imagecheck-image" src="./assets/background/${key}.png" alt="${value.name}" title="${value.name}" data-bs-toggle="tooltip"/>
                </span>
            </label>
        </div>
        `;
        backgrounds_div.append(bg_html);
    }
}
function initCharacters() {
    // 渲染角色选择
    let characters_div = $("#characters_div");
    characters_div.empty();
    for (const [key, value] of Object.entries(mahoshojo)) {
        let char_html = `
        <div class="col-auto">
            <label class="form-imagecheck mb-2">
                <input name="character" type="radio" value="${key}" class="form-imagecheck-input" onchange="initEmotions('${key}');updateCanvas()"${key=="sherri" ? " checked" : ""}/>
                <span class="form-imagecheck-figure">
                    <span class="avatar avatar-xl" style="background-image: url('./assets/chara/${key}/${key} (1).png')" title="${value.name}" data-bs-toggle="tooltip"></span>
                </span>
            </label>
        </div>
        `;
        characters_div.append(char_html);
    }
}
function initEmotions(character) {
    // 渲染表情选择
    let emotions_div = $("#emotions_div");
    emotions_div.empty();
    for (i=1; i<mahoshojo[character].emotion_count; i++) {
        let emotion_html = `
        <div class="col-auto">
            <label class="form-imagecheck mb-2">
                <input name="emotion" type="radio" value="${i}" class="form-imagecheck-input" onchange="updateCanvas()" />
                <span class="form-imagecheck-figure">
                    <img class="form-imagecheck-image avatar avatar-xl" src="./assets/chara/${character}/${character} (${i}).png"/>
                </span>
            </label>
        </div>
        `;
        emotions_div.append(emotion_html);
    }
    $('input[name="emotion"]').first().click();
}
function updateCanvas() {
    let canvas = $('#canvas')[0];
    let ctx = canvas.getContext("2d");
    
    if ($('input[name="background"]:checked')) ctx.drawImage($('input[name="background"]:checked').next().children()[0], 0, 0, canvas.width, canvas.height);
    
    let character = $('input[name="character"]:checked').val();
    if (character) {
        if ($('input[name="emotion"]:checked')) ctx.drawImage($('input[name="emotion"]:checked').next().children()[0], 0, 134);
        for (const [key, value] of Object.entries(text_configs_dict[character])) {
            ctx.font = `${value.font_size}px 华文中宋`;

            ctx.fillStyle = `rgb(${shadow_color[0]}, ${shadow_color[1]}, ${shadow_color[2]})`;
            ctx.fillText(value.text, value.position[0] + shadow_offset[0], value.font_size + value.position[1] + shadow_offset[1]);

            ctx.fillStyle = `rgb(${value.font_color[0]}, ${value.font_color[1]}, ${value.font_color[2]})`;
            ctx.fillText(value.text, value.position[0], value.font_size + value.position[1]);
        }
    }

    let text = $('input[name="text"]').val();
    if (text) {
        let text_font_size = parseInt($('input[name="text_font_size"]').val());
        ctx.font = `${text_font_size}px 华文中宋`;
        
        // 自动换行绘制
        const maxWidth = text_over[0] - text_postion[0];
        const maxHeight = text_over[1] - text_postion[1];
        const lineHeight = Math.floor(text_font_size * 1.2);
        const maxLines = Math.floor(maxHeight / lineHeight) || 1;
        let lines = [];

        // 根据空格进行单词换行，若无空格则按字符换行（适合中文）
        if (text.indexOf(' ') !== -1) {
            const words = text.split(' ');
            let line = '';
            for (let n = 0; n < words.length; n++) {
                const testLine = line ? (line + ' ' + words[n]) : words[n];
                const testWidth = ctx.measureText(testLine).width;
                if (testWidth > maxWidth && line) {
                    lines.push(line);
                    line = words[n];
                    if (lines.length >= maxLines) break;
                } else {
                    line = testLine;
                }
            }
            if (lines.length < maxLines && line) lines.push(line);
        } else {
            let line = '';
            for (let i = 0; i < text.length; i++) {
                const ch = text[i];
                const testLine = line + ch;
                const testWidth = ctx.measureText(testLine).width;
                if (testWidth > maxWidth && line) {
                    lines.push(line);
                    line = ch;
                    if (lines.length >= maxLines) break;
                } else {
                    line = testLine;
                }
            }
            if (lines.length < maxLines && line) lines.push(line);
        }

        // 绘制每一行（先阴影再主体）
        for (let i = 0; i < Math.min(lines.length, maxLines); i++) {
            const line = lines[i];
            const x = text_postion[0];
            // 保持与原来单行位置一致：首行基线为 text_font_size + text_postion[1]
            const y = text_font_size + text_postion[1] + i * lineHeight;

            ctx.fillStyle = `rgb(${shadow_color[0]}, ${shadow_color[1]}, ${shadow_color[2]})`;
            ctx.fillText(line, x + shadow_offset[0], y + shadow_offset[1]);

            ctx.fillStyle = `rgb(255, 255, 255)`;
            ctx.fillText(line, x, y);
        }
    }
}
function downloadImage() {
    let canvas = $('#canvas')[0];
    canvas.toBlob(function(blob) {
        saveAs(blob, `魔裁文本框表情-${Date.now()}.png`);
    });
}
function init() {
    initBackgrounds();
    initCharacters();
    initEmotions('sherri');
}