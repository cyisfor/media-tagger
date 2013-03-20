with a(id) AS (
    with b(id) AS (
        SELECT 42
    ) select id from b
) select id from a;
