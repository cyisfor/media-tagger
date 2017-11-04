while sleep 1; do 
    { 
        echo '\pset format unaligned'
        echo '\pset tuples_only on'
        echo "select count(1) FROM findDupes(0.4, '30 seconds'::interval)"
    } | psql pics | tail -n1 | grep -q '^0$' && break; 
done
