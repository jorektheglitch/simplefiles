const files = document.getElementById("files");
const explanation = document.getElementById("explanation");

const _SIZES = [
	['',  10**0],

	['k', 10**3],
	['M', 10**6],
	['G', 10**9],
	['T', 10**12],
	['P', 10**15],
	['E', 10**18],
	['Z', 10**21],
	['Y', 10**24],
	['R', 10**27],
	['Q', 10**30]
];

function asHumanReadable(value, unit, precision = 2) {
	let size = value;
	let unitPrefix = '';
	for (let [prefix, divisor] of _SIZES) {
		size = value / divisor;
		if (size < 1000) {
			unitPrefix = prefix;
			break;
		};
	};
	let precisionDivisor = 10**precision;
	size = Math.ceil(size * precisionDivisor) / precisionDivisor;
	return `${size}${unitPrefix}${unit}`;
}

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
		const speedEl = createElement('pre', {style: {'grid-area': 'speed'}});
		const cancelBtn = createElement('button', {class: 'upload-cancel'});
		const cancelImage = createElement('img', {style: {height: '100%'}});
		cancelImage.src = './pictograms/cancel.svg';
		cancelBtn.append(cancelImage);
		const fileLink = createElement("a", {class: 'file-link'});
		fileLink.append(document.createTextNode(name));
		container.append(fileLink, progressEl, speedEl, cancelBtn);
		files.append(container);
		files.hidden = false;
		xhr.open("POST", "/api/store");
		cancelBtn.onclick = (click) => {
			xhr.abort();
		}
		xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem("token")}`);
		xhr.upload.onprogress = (progress) => {
			const {loaded, total} = progress;
			progressEl.max = total;
			progressEl.value = loaded;
			const currentTime = new Date();
			const timeDeltaMs = currentTime - lastActve;
			const loadedDelta = loaded - lastLoaded;
			const speed = loadedDelta*1000 / timeDeltaMs;
			speedEl.innerHTML = asHumanReadable(speed, 'B/s');
			//let percents = (loaded/total*100).toFixed(2);
			//console.log(`Loaded ${percents}% (${loaded}/${total})`);
			lastActve = currentTime;
			lastLoaded = loaded;
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
			speedEl.remove();
		};
		xhr.onerror = xhr.onabort = (event) => {
			const retryBtn = getRetryButton();
			cancelBtn.replaceWith(retryBtn);
            progressEl.classList.add("failed");
			speedEl.remove();
        };
		let lastActve = new Date();
		let lastLoaded = 0;
		xhr.send(data);
	};
	file.click();
}
