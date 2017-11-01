var queue = {};
var timeout = null;

function setsrcs() {
	let myqueue = queue;
	queue = {};
	for(let src in myqueue) {
		let img = myqueue[src];
		let x = new XMLHttpRequest();
		x.addEventListener("load",function(e) {
			console.log("loaded",e);
			img.src = src;
		},true);
		x.open("GET", img.json);
		x.send();
	}
	timeout = null;
}

function reload_later(dest,src,json) {
	var img = document.createElement('img');
	img.json = json;
	img.style.height = '190px';
	img.addEventListener('error', function(e) {
		queue[src] = img;
		if(timeout != null)
			clearTimeout(timeout);
		timeout = setTimeout(setsrcs,3000);
	},false);
	img.addEventListener('load',function() {
		img.style.height = '';
		dest.parentNode.replaceChild(img,dest);
	},false);
	img.src = src;
}
