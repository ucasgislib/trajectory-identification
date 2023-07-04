# trajectory-identification
Abnormal trajectory identification method


python step1_links2points.py ./mudanyuan/data/aoi.shp ./mudanyuan/data/tracking_links.shp ./mudanyuan/result/tracking_points.shp

python step2_point_entropy.py ./mudanyuan/result/tracking_points.shp ./mudanyuan/data/tracking_links.shp ./mudanyuan/result/tracking_points.shp 35 0 -1

python step3_point_linedensity_gradient.py ./mudanyuan/result/tracking_points1.shp ./mudanyuan/data/tracking_links.shp ./mudanyuan/result/tracking_points.shp 35 0 -1

python step4_point_type.py  ./mudanyuan/result/tracking_points.shp ./sample/sample_points.shp ./mudanyuan/result/tracking_points.shp 0.135 l2 0.03 lg

python step5_link_endpoint_type.py  ./mudanyuan/data/tracking_links.shp ./mudanyuan/result/tracking_points.shp ./mudanyuan/result/tracking_links.shp

python step6_link_endpoint_onsite_heading.py ./mudanyuan/result/tracking_links.shp ./mudanyuan/result/tracking_links.shp 35

python step7_link_line_density.py ./mudanyuan/result/tracking_links.shp ./mudanyuan/result/tracking_links.shp 35

python step8_link_spatial_reasoning.py ./mudanyuan/result/tracking_links.shp ./mudanyuan/result/tracking_links.shp 27 0.33
