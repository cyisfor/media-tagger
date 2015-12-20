function round(f) {
	return Math.round(f*100)/100.0;
}

document.addEventListener('DOMContentLoaded',function() {
	var status = document.createElement('div');
	status.content = document.createTextNode('status');
	status.appendChild(status.content);
	status.style.display = 'none';
	status.style.backgroundColor='yellow';
	status.style.position = 'absolute';
	status.style.top = '1%';
	status.style.left = '1%';
	var img = document.getElementById('img');
	function present(n,d) {
		return Math.round(n*10000/d)/100.0 + '%';
	}
	document.body.appendChild(status);
	var save = {};
	img.addEventListener('click',function(e) {
		if(e.ctrlKey) {
			e.preventDefault();
			status.style.backgroundColor = 'pink';
			save.left = e.clientX - img.offsetLeft;
			save.top = e.clientY - img.offsetTop;
			return false;
		}
	},true);
	img.addEventListener('mousemove',function(e) {
		if (e.ctrlKey) {
			status.style.display = 'inline';
			var left = (e.clientX-img.offsetLeft);
			var top = (e.clientY-img.offsetTop);
			var w = img.clientWidth;
			var h = img.clientHeight;
			if(save.left) {
				status.content.nodeValue = "top = '"+present(save.top,h)+"', "+
					"derpleft = '"+present(save.left,w)+"', "+
					"w = '"+present(left-save.left,w)+"', h = '"+present(top-save.top,h)+"'";
			} else {
				status.content.nodeValue = '('+present(top,h)+','+present(left,w)+')';
			}
			return true;
		}
		return false;
	},false);
},true);
