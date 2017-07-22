CREATE TABLE explanations (
	   id bigserial PRIMARY KEY,
	   image INTEGER REFERENCES images(id) ON UPDATE CASCADE ON DELETE CASCADE NOT NULL,
	   -- these can be xx%
	   top TEXT NOT NULL,
	   derpleft TEXT NOT NULL,
	   w TEXT NOT NULL,
	   h TEXT NOT NULL,
	   script TEXT NOT NULL);
CREATE UNIQUE INDEX unique_explanations ON explanations(image,top,derpleft,w,h);
-- but what about movies? time based script format? time column?
