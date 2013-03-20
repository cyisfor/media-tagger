LISTEN info;
\echo 'writing image'
COPY image (id) TO '/dev/shm/convert/image';
\echo 'writing tag'
COPY tag (id,name) TO '/dev/shm/convert/tag';
\echo 'writing image_tag'
COPY image_tag (image,tag) TO '/dev/shm/convert/it';
\echo 'writing image w/ media and image info'
COPY image (id,name,hash,created,added,size,type,md5,thumbnailed,animated,width,height,ratio) TO '/dev/shm/convert/media';
\echo 'writing sources'
COPY source (id,image,uri,code,checked) TO '/dev/shm/convert/sauce';
\echo 'BOOP'
COPY filesource (id,path) TO '/dev/shm/convert/filesauce';
