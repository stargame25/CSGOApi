let xhr = new XMLHttpRequest();
let mainForm = document.getElementById("login");
let F2AtitleText = document.getElementsByClassName("title")[1];
let logginScreen = document.getElementById("login");
let f2aScreen = document.getElementById("f2a");
let usernameInput = document.getElementById("username");
usernameInput.onkeypress = enterTrigger;
let passwordInput = document.getElementById("password");
passwordInput.onkeypress = enterTrigger;
let captchaInput = document.getElementById("captchaInput");
captchaInput.onkeypress = enterTrigger;
let codeInput = document.getElementById("f2aCode");
codeInput.onkeypress = enterTriggerF2A;
let errorDiv = document.getElementById("error");
let captchaDiv = document.getElementById("captcha");
let mod, exp, type, captchaGid, captchaUrl, captcha;
let submitButton = document.getElementById("submitButton");
let submitButtonF2A = document.getElementById("submitF2A");
let loader = document.getElementById("loader");

function validLogin(){
    if(Boolean(captchaGid) && Boolean(captchaUrl)){
        if(!Boolean(captchaInput.value)){
            return false;
        }
    }
    let usernameInput = document.getElementById("username");
    let passwordInput = document.getElementById("password");
    return Boolean(usernameInput.value) && Boolean(passwordInput.value);
}

function validF2A(){
    return Boolean(codeInput.value);
}

function startLogging(){
    if(Boolean(captchaGid)){
        captchaDiv.hidden = true;
    }
    errorDiv.hidden = true;
    stateLoginForm(true);
    togglePreloader();
}

function togglePreloader(state=true){
    if(state){
        loader.style.display = "flex";
    } else {
        loader.style.display = "none";
    }
}


function showError(error){
    let errorSpan = errorDiv.getElementsByTagName("span")[0];
    let clonedSpan = errorSpan.cloneNode();
    if(errorSpan){
        errorSpan.remove()
    }
    clonedSpan.textContent = error;
    errorDiv.appendChild(clonedSpan);
    errorDiv.hidden = false;
    togglePreloader(false);
}

function showCaptcha(){
    captchaDiv.hidden = false;
    captchaDiv.getElementsByTagName("img")[0].src = captchaUrl;
}

function logginFailure(error){
    showError(error);
    if(Boolean(captchaGid)){
        showCaptcha();
    }
    stateLoginForm(false);
    usernameInput.value = "";
    passwordInput.value = "";
    captchaInput.value = "";
    codeInput.value = "";
    submitButtonF2A.disabled = false;
    codeInput.disabled = false;
    f2aScreen.hidden = true;
    logginScreen.hidden = false;
}

function stateLoginForm(state){
    submitButton.disabled = state;
    usernameInput.disabled = state;
    passwordInput.disabled = state;
    captchaInput.disabled = state;
}

function stateF2AForm(state){
    codeInput.disabled = state;
    submitButtonF2A.disabled = state;
}

function encrypt(password, mod, exp){
    let publicKey = RSA.getPublicKey(mod, exp);
    return RSA.encrypt(password.replace(/[^\x00-\x7F]/g, ''), publicKey);
}


function loginIn(){
    if(!validLogin()){
        showError("Не всі поля заповнені");
        return;
    }
    startLogging();
    let username = usernameInput.value;
    let password = passwordInput.value;
    let data = new FormData();
    data.append("username", username);
    xhr.open('POST', '/getrsa');
    xhr.onload = function() {
        if (xhr.status === 200) {
            let rsaData = JSON.parse(xhr.response);
            mod = rsaData.publickey_mod;
            exp = rsaData.publickey_exp;
            timestamp = rsaData.timestamp;
            let encryptedData = encrypt(password, mod, exp);
            data = new FormData();
            data.append("username", username);
            data.append("password", encryptedData);
            data.append("timestamp", timestamp);
            if (Boolean(captchaGid)) {
                data.append("captcha", captchaInput.value);
                data.append("captcha_gid", captchaGid);
            }
            xhr.open('POST', '/login');
            xhr.onload = function () {
                if (xhr.status === 200) {
                    let response = JSON.parse(xhr.response);
                    if (Number(response.code) === 1) {
                        window.location.replace(window.location.href)
                    } else if (Number(response.code) === 2 || Number(response.code) === 3) {
                        if (Number(response.code) === 3) {
                            F2AtitleText.textContent = "2FA";
                        } else {
                            F2AtitleText.textContent = "Steam Guard";
                        }
                        type = Number(response.code);
                        f2aScreen.hidden = false;
                        logginScreen.hidden = true;
                        togglePreloader(false);
                    } else if (Number(response.code) === 4) {
                        type = Number(response.code);
                        captchaGid = response.captcha_gid;
                        captchaUrl = response.captcha_url;
                        showError("Введіть каптчу");
                        stateLoginForm(false);
                        showCaptcha();
                        captchaInput.focus();
                    } else if (Number(response.code) === -1) {
                        logginFailure("Забагато спроб входу");
                    } else {
                        logginFailure("Неправильний логін або пароль");
                    }
                } else {
                    logginFailure("З'єднання з сервером відсутнє");
                    return null;
                }
            };
            xhr.send(data);
        } else {
            logginFailure("Помилка сервера");
            return null;
        }
    };
    xhr.send(data);
}

function twoFactorIn(){
    if(!validF2A()){
        showError("Введіть код аунтефікації");
        return;
    }
    stateF2AForm(true);
    togglePreloader();
    let username = usernameInput.value;
    let password = passwordInput.value;
    let code = codeInput.value;
    let data = new FormData();
    let encryptedData = encrypt(password, mod, exp);
    data.append("username", username);
    data.append("password", encryptedData);
    data.append("timestamp", timestamp);
    if(type === 2){
        data.append("email_code", code);
        data.append("emailsteamid", code);
    } else if (type === 3){
        data.append("twofactor_code", code);
    }
    xhr.open('POST', '/login');
    xhr.onload = function(){
        if (xhr.status === 200) {
            let response = JSON.parse(xhr.response);
            if(Number(response.code) === 1){
                window.location.replace(window.location.href)
            } else if(Number(response.code) === 0) {
                logginFailure("Помилка в введених даних");
                return null;
            } else if (Number(response.code) === type){
                stateF2AForm(false);
                showError("Не правильний код аунтефікації");
                codeInput.focus();
                codeInput.textContent = "";
            }
        } else {
            stateF2AForm(false);
            logginFailure("Помилка ключа шифрування");
            return null;
        }
    };
    xhr.send(data);
}

function enterTrigger({keyCode}){
    if(keyCode == 13){
        submitButton.click();
    }
}

function enterTriggerF2A({keyCode}){
    if(keyCode == 13){
        submitButtonF2A.click();
    }
}