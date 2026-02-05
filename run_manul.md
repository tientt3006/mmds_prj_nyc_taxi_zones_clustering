bash start-dfs.sh
bash start-yarn.sh
bash start-master.sh
bash start-workers.sh
jps
ssh worker1 "jps"

source mmds-venv/bin/activate
bash run...



--- Safe Stop---
stop-yarn.sh
stop-dfs.sh



1% Sample 	build_graph 	0.01 	444540.0 	394636.0 	19283 	32.371574 	0.539526 	2026-02-05T16:23:57.394763 	NaN 	NaN 	NaN 	NaN 	NaN
1 	5% Sample 	build_graph 	0.05 	2221743.0 	1972346.0 	33051 	3.328913 	0.055482 	2026-02-05T16:24:00.723729 	NaN 	NaN 	NaN 	NaN 	NaN
2 	PageRank 1% 	pagerank 	0.01 	NaN 	NaN 	19349 	NaN 	NaN 	2026-02-05T16:24:12.063886 	257.0 	5.0 	7.243359 	10.954295 	0.182572
