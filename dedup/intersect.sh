while sleep 1; do 
    { 
        echo '\pset format unaligned'
        echo '\pset tuples_only on'
        echo 'select findDupes(0.4)'
    } | psql -h /run -p 5433 pics | tail -n1 | grep -q '^0$' && break; 
done
