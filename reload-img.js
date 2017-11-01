var queue = {};
var timeout = null;

function setsrcs() {
	let myqueue = queue;
	queue = {};
	for(let src in myqueue) {
		let img = myqueue[src];
		img.src = src;
	}
	timeout = null;
}

function reload_later(dest,src) {
	var img = document.createElement('img');
	img.style.height = '190px';
	img.addEventListener('error', function(e) {
		queue[src] = img;
		if(timeout != null)
			clearTimeout(timeout);
		timeout = setTimeout(setsrcs,1000);
	},false);
	img.addEventListener('load',function() {
		img.style.height = '';
		dest.parentNode.replaceChild(img,dest);
	},false);
	setsrc()
}
