// All exports must be at the top level
export function make_module(co) {
    const coDiv = document.createElement('div');
    coDiv.classList.add('co');
    coDiv.classList.add('module');
    coDiv.classList.add(co.type);
    coDiv.innerHTML = "<div class='module_contents no_contents'></div>";
    return coDiv;
}

export function inject_content_into_element(element, content_container_class, content) {
    let contentContainer = element.querySelector(content_container_class);
    contentContainer.innerHTML = content;
    contentContainer.classList.add('has_contents');
    contentContainer.classList.remove('no_contents');
}

export function header(label) {
    return "<span class='header'>" + label + "</span>";
}

export function body_text(contents) {
    return "<div class='conversation-body-text'>" + contents + "</div>";
}

export function data_text(contents) {
    return "<div class='conversation-data-text info-text-style'>" + contents + "</div>";
}

export function get_or_create_difficulty_element(analysisDiv) {
    const difficultyElement = analysisDiv.querySelector('.difficulty_element');
    if (difficultyElement) {
        return difficultyElement;
    } else {
        const difficultyElement = document.createElement('div');
        difficultyElement.classList.add('difficulty_element', 'prescene_contents');
        difficultyElement.innerHTML = header("Difficulty") + "<div class='difficulty_analysis info-text-style no_contents'></div><div class='prescene_footer'><span class='difficulty_target info-text-style no_contents'></span><span class='difficulty_roll info-text-style no_contents'></span></div>";
        analysisDiv.appendChild(difficultyElement);
        return difficultyElement;
    }
}

export function get_or_create_world_reveal_element(analysisDiv) {
    const difficultyElement = analysisDiv.querySelector('.world_reveal_element');
    if (difficultyElement) {
        return difficultyElement;
    } else {
        const difficultyElement = document.createElement('div');
        difficultyElement.classList.add('world_reveal_element', 'prescene_contents');
        difficultyElement.innerHTML = header("World Reveal") + "<div class='world_reveal_analysis info-text-style no_contents'></div><div class='prescene_footer'><span class='world_reveal_level info-text-style no_contents'></span><span class='world_reveal_roll info-text-style no_contents'></span></div>";
        analysisDiv.appendChild(difficultyElement);
        return difficultyElement;
    }
}

export function determine_difficulty_color(difficultyElement, rolledValue) {
    const targetElement = difficultyElement.querySelector('.difficulty_target');
    const targetText = targetElement ? targetElement.textContent.replace('Target', '').trim() : null;
    let targetValue, degreeOfSuccess, degreeOfFailure, l;
    
    if (!isNaN(parseInt(targetText))) {
        console.debug("targetText is a number");
        targetValue = parseInt(targetText);
        if (rolledValue >= targetValue) {
            degreeOfSuccess = (rolledValue - targetValue) / (100 - targetValue);
            l = degreeOfSuccess * 43;
            return 'hsl(140,' + l + '%, 10%)';
        } else {
            degreeOfFailure = (targetValue - rolledValue) / targetValue;
            l = degreeOfFailure * 43;
            return 'hsl(359,' + l + '%, 10%)';
        }
    } else {
        console.debug("targetText is not a number");
        return 'hsl(180, 43%, 10%)';
    }
}

export function determine_world_reveal_color(worldRevealElement, rolledValue) {
    console.debug("determining world reveal color");
    console.debug("rolledValue: ", rolledValue);
    console.debug("worldRevealElement: ", worldRevealElement);
    const targetElement = worldRevealElement.querySelector('.world_reveal_level');
    const targetText = targetElement ? targetElement.textContent.replace('Level', '').trim() : null;
    const targetValue = targetText;
    let degreeOfSuccess, degreeOfFailure, l;
    
    console.debug("targetValue: ", targetValue);
    if (targetValue.toLowerCase().trim() === "n/a") {
        return 'hsl(0, 0%, 10%)';
    } else if (targetValue.toLowerCase().trim() === "light") {
        if (rolledValue >= 95) {
            console.debug("light success");
            return 'hsl(140, 21%, 10%)';
        } else if (rolledValue <= 5) {
            console.debug("light failure");
            return 'hsl(359, 21%, 10%)';
        } else {
            console.debug("light neutral");
            return 'hsl(0, 0%, 10%)';  
        }
    } else if (targetValue.toLowerCase().trim() === "moderate") {
        if (rolledValue >= 66) {
            degreeOfSuccess = (rolledValue - 66) / (100 - 66);
            l = degreeOfSuccess * 43;
            return 'hsl(140,' + l + '%, 10%)';
        } else if (rolledValue <= 33) {
            degreeOfFailure = (66 - rolledValue) / 66;
            l = degreeOfFailure * 43;
            return 'hsl(359,' + l + '%, 10%)';
        } else {
            return 'hsl(0, 0%, 10%)';
        }
    } else if (targetValue.toLowerCase().trim() === "strong") {
        if (rolledValue > 50) {
            degreeOfSuccess = (rolledValue - 50) / (100 - 50);
            l = degreeOfSuccess * 43;
            return 'hsl(140,' + l + '%, 10%)';
        } else if (rolledValue < 50) {
            degreeOfFailure = (50 - rolledValue) / 50;
            l = degreeOfFailure * 43;
            return 'hsl(359,' + l + '%, 10%)';
        }
    }
    return 'hsl(0, 0%, 10%)';  // Default return
}

export function render_difficulty_and_world_reveal_object(difficulty_and_world_reveal_object) {   
    let rendered_world_reveal_object = difficulty_and_world_reveal_object.difficulty.difficulty_analysis + "\n\n" + 
        difficulty_and_world_reveal_object["world reveal"].world_reveal_analysis + "\n\n";
    rendered_world_reveal_object += "Difficulty Target: " + difficulty_and_world_reveal_object.difficulty.difficulty_target + 
        "\n\n" + "World Reveal Level: " + difficulty_and_world_reveal_object["world reveal"].world_reveal_level + "\n\n";
    return rendered_world_reveal_object;
}