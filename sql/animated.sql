SELECT connectManyToOne(array(SELECT id FROM images WHERE animated IS TRUE),findTag('animated'));
