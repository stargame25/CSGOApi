let xhr = new XMLHttpRequest();
function submit(){
    let form = {};
    let sections = [...document.querySelectorAll('.settingSection > div')];
    sections.forEach(category => {
        let data = serialize(category.querySelectorAll("[name]:not(meta)"));
        let temp = {};
        for(let key in data){
            temp[key] = data[key]
        }
        form[category.className.replace("Section", "")] = temp;
    });
    console.log(JSON.stringify(form))
    xhr.open('POST', '/settings');
    xhr.onload = function() {
        if (xhr.status === 200) {
            window.location.reload()
        }
    };
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.send(JSON.stringify(form));
}

function serialize(nodeList){
    const result = {};
    const typeList = {};
    const names = [...new Set([].map.call(nodeList, function(item){
        typeList[item.name] = item.type;
        return item.name;
    }))];
    names.forEach(name => {
        if(typeList[name] === 'radio'){
            let arrayValue = [].filter.call(nodeList, item => item.name === name && item.checked);
            if(arrayValue.length === 1){
                if(arrayValue[0].value === 'on'){
                    result[name] = true;

                } else if (arrayValue[0].value === 'off'){
                    result[name] = false;

                } else {
                    result[name] = arrayValue[0].value;
                }
            }
        } else if(typeList[name] === 'checkbox') {
            let arrayValue = [].filter.call(nodeList, item => item.name === name && item.checked);
            arrayValue.forEach(item => {
                result[item.value] = item.checked;
            })
        } else {
            let arrayValue = [].filter.call(nodeList, item => item.name === name);
            arrayValue.forEach(item => {
                if(isNaN(Number(item.value))){
                    result[name] = item.value;
                } else {
                    result[name] = Number(item.value);
                }
            })
        }
    });
    return result
}