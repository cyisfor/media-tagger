while sleep 1; do 
    { 
        echo '\pset format unaligned'
        echo '\pset tuples_only on'
        echo 'select findDupes(1000000)'
    } | psql -p 5433 pics; 
    exit 3
done
