const files = document.getElementById("files");
const explanation = document.getElementById("explanation");

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

function getRetryButton(onclick) {
	const retryBtn = createElement('button', {class: 'retry-btn'});
	const retryImage = createElement('img', {style: {height: '100%'}});
	retryImage.src = './pictograms/retry.svg';
	retryBtn.append(retryImage);
	if (onclick) {
		retryBtn.onclick = onclick;
	};
	return retryBtn;
}

document.getElementById("fileLoadButton").onclick = (click) => {
	click.preventDefault();
	const form = document.createElement('form');
	const file = document.createElement('input');
	file.name = "file";
	file.type = "file";
	form.append(file);
	file.onchange = (change) => {
		explanation.remove();
		const name = file.files[0].name;
		const data = new FormData(form);
		const xhr = new XMLHttpRequest();
		const container = createElement('div', {class: 'file-container'});
		const progressEl = createElement('progress', {class: 'upload-progress'});
		const cancelBtn = createElement('button', {class: 'upload-cancel'});
		const cancelImage = createElement('img', {style: {height: '100%'}});
		cancelImage.src = './pictograms/cancel.svg';
		cancelBtn.append(cancelImage);
		const fileLink = createElement("a", {class: 'file-link'});
		fileLink.append(document.createTextNode(name));
		container.append(fileLink, progressEl, cancelBtn);
		files.append(container);
		files.hidden = false;
		xhr.open("POST", "/api/store");
		cancelBtn.onclick = (click) => {
			xhr.abort();
		}
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
				const retryBtn = getRetryButton();
				cancelBtn.replaceWith(retryBtn);
                progressEl.classList.add("failed");
				return;
			}
			const info = JSON.parse(xhr.response);
			fileLink.href = "./file.html#";
			const copyBtn = createElement('button', {class: 'copy-btn'});
			const copyImage = createElement('img', {style: {height: '100%'}});
			copyImage.src = './pictograms/copy.svg';
			copyBtn.append(copyImage);
			cancelBtn.replaceWith(copyBtn);
			progressEl.remove();
		};
		xhr.onerror = xhr.onabort = (event) => {
			const retryBtn = getRetryButton();
			cancelBtn.replaceWith(retryBtn);
            progressEl.classList.add("failed");
        };
		xhr.send(data);
	};
	file.click();
}
