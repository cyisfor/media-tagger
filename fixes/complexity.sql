UPDATE tags SET complexity = greatest(complexity,1) where name LIKE '%:%';
