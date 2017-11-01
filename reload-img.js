var queue = {};
var timeout = null;

function setsrcs() {
	let myqueue = queue;
	queue = {};
	function jssucks(src,img) {
		let x = new XMLHttpRequest();
		x.addEventListener("load",function(e) {
			img.src = src;
		},true);
		x.open("GET", img.json + '?' + (new Date()).getTime());
		x.send();
	}

	for(let src in myqueue) {
		jssucks(src, myqueue[src]);
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
