function reload_later(dest,src) {
	var img = document.createElement('img');
	img.style.height = '219px';
	function setsrc() {
		img.src = src;
	}
	img.addEventListener('error', function(e) {
		setTimeout(setsrc,1000);
	},false);
	img.addEventListener('load',function() {
		dest.parentNode.replaceChild(img,dest);
	},false);
	setsrc()
}
