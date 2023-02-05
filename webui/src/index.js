function isObject(obj) {
	return typeof obj === 'object' && obj !== null;
};

function isArray(obj) {
	return obj instanceof Array;
};

function createElement(tagName, {classList, style, ...options} = {}) {
	let el = document.createElement(tagName);
	if (isArray(classList)) {
		classList.map(className=>el.classList.add(className));
	};
	if (isObject(style)) {
		let styles = el.style;
		Object.entries(style).forEach(([name, value]) => {
			styles.setProperty(name, value);
		});
	};
	if (options.class) {
		el.classList.add(options.class);
	};
	return el;
};

document.getElementById("fileLoadButton").onclick = (click) => {
	click.preventDefault();
	const filesList = document.getElementById("filesList");
	const form = document.createElement('form');
	const file = document.createElement('input');
	file.name = "file";
	file.type = "file";
	form.append(file);
	file.onchange = (change) => {
		const name = file.files[0].name;
		const data = new FormData(form);
		const xhr = new XMLHttpRequest();
		const container = createElement('div', {class: 'attachment-container'});
		const nameEl = createElement('h5', {class: 'attachment-name'} );
		const progressEl = document.createElement('progress')
		document.createElement('div').style.grid
		const del = createElement('button', {class: 'attachment-delbtn'});
		const delImage = createElement('img', {style: {height: '100%'}});
		delImage.src = 'images/pictorgams/close.svg';
		del.append(delImage);
		nameEl.append(document.createTextNode(name));
		container.append(nameEl, del, progressEl);
		filesList.append(container);
		filesList.hidden = false;
		xhr.open("POST", "/api/store");
		xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem("token")}`);
		xhr.upload.onprogress = (progress) => {
			let {loaded, total} = progress;
			progressEl.max = total;
			progressEl.value = loaded;
			//let percents = (loaded/total*100).toFixed(2);
			//console.log(`Loaded ${percents}% (${loaded}/${total})`);
		};
		xhr.onload = (event) => {
			if (xhr.status!=200) {
				console.error(`File load request failed with status ${xhr.status} (${xhr.statusText})`);
                progressEl.classList.add("failed");
				return;
			}
			const info = JSON.parse(xhr.response);
			let ids = [];
			if (attachments.value.trim())
				ids = attachments.value.split(" ");
			ids.push(info.file.id);
			attachments.value = ids.join(" ");
			progressEl.remove();
		};
		xhr.onerror = (event) => {
            progressEl.classList.add("failed");
        };
		xhr.send(data);
	};
	file.click();
}
