The following python codes may detect various types of shortcut tracking links by our proposed spatial reasoning method. The step-by-step operations are listed as follows:
  
0. Dependencies
This program requires the following dependencies:
numpy (>=1.16.6+mkl)
scipy (>=1.2.3) 
matplotlib (>=2.2.5)
pandas (>=0.24.2)
sklearn (0.20.3)
Rtree (>=0.9.3)
GDAL (>=3.0.2)

1. step1_links2points.py
Given a set of tracking links, this program will convert links to the points that make up the links. Whether each point is in the aoi is also judged in the program.

Usage:
python step1_links2points.py
usage: Usage: python step1_links2points.py <aoi> <tracking_links> <tracking_points>
<aoi> - a shape file containing the area of intersecting
<tracking_links> - a shape file containing tracking links at a specific experiment area
<tracking_points> -  a shape file containing tracking points at a specific experiment area

Example:
python step1_links2points.py ./mudanyuan/data/aoi.shp ./mudanyuan/data/tracking_links.shp ./mudanyuan/result/tracking_points.shp
2. step2_pnt_entropy.py
Given a set of tracking points, this program will compute the information entropy for each point. The entropy value is high for a point close to an intersection while it is low for those on roads.

Usage:
python step2_pnt_entropy.py
usage: python step2_point_entropy.py <tracking_points> <tracking_links> <entropy> <window> <start> <end>
<tracking_points> - a shape file containing tracking points at a specific experiment area
<tracking_links> - a shape file containing tracking links at a specific experiment area
<entropy> - a shape file that is same as the input tracking_points file but add a newly calculated "entropy" field 
<window> - the size of a search window that is used to for select those intersected links for an onsite-heading calculation, the default is 35 meters (close to a road width)
<start> - start-point of the calculations
<end> - end-point of the calculations, where -1 for the last point

Example:
python step2_point_entropy.py ./mudanyuan/result/tracking_points.shp ./mudanyuan/data/tracking_links.shp ./mudanyuan/result/tracking_points1.shp 35 0 -1

3. step3_point_linedensity_gradient.py
Given a set of tracking points, this program will compute the density gradient for each point. 

Usage:
python step3_point_linedensity_gradient.py
usage: python step3_point_linedensity_gradient.py <tracking_points> <tracking_links> <grad> <window> <start> <end>
<tracking_points> - a shape file containing tracking points at a specific experiment area
<tracking_links> - a shape file containing tracking links at a specific experiment area
<grad> - a shape file that is same as the input tracking_points file but add a newly calculated "grad" field 
<window> - the size of a search window that is used to for select those intersected links for an onsite-heading calculation, the default is 35 meters (close to a road width)
<start> - start-point of the calculations
<end> - end-point of the calculations, where -1 for the last point

Example:
python step3_point_linedensity_gradient.py ./mudanyuan/result/tracking_points1.shp ./mudanyuan/data/tracking_links.shp ./mudanyuan/result/tracking_points2.shp 35 0 -1


4. step4_pnt_type.py
This program classifies tracking points into two groups ("on-crossroads" vs "on-road") by information entropy of points using a logistic regression model. The regression model is trained using a set of 1000 sample points pre-collected in a large database in advance.

Usage:
python step4_pnt_type.py 
usage: python step4_point_type.py <entropy> <training> <labeled> <C> <penalty> <percentile> <method>
<entropy> - a tracking point shape file containing an "entropy" field
<training> - a shape file containing the sample points of road points and inetrsection points 
<labeled> - a shape file that is same as the input entropy file but add a newly calculated "labeled" field. 0 is an on-road points and 1 denotes to an on-crossroads point
<C> - reciprocal of the regularization coefficient λ
<penalty>  - used to specify the benchmark for punishment
<percentile> - threshold of low-density undecidable percentile
<method> - method for the classification

Example:
python step4_point_type.py  ./mudanyuan/result/tracking_points2.shp ./sample/sample_points.shp ./mudanyuan/result/tracking_points3.shp 0.135 l2 0.05 lg

5. step5_link_endpoint_type.py
give the endpoint_type of the links.

Usage:
python step5_link_endpoint_type.py 
usage: python step4_link_endpoint_type.py <tracking_links> <tracking_points> <endpoint_type>
<tracking_points> - a shape file containing tracking points at a specific experiment area
<tracking_links> - a shape file containing tracking links at a specific experiment area
<endpoint_type> - a shape file containing the two end-points type of all the tracking links at a specific experiment area

Example:
python step5_link_endpoint_type.py  ./mudanyuan/data/tracking_links.shp ./mudanyuan/result/tracking_points3.shp ./mudanyuan/result/tracking_links1.shp

6. step6_link_endpoint_onsite_heading.py
Estimating the on-site headings of two endpoints that form a track link

Usage: python step5_link_endpoint_onsite_heading.py
usage: python step5_link_endpoint_onsite_heading.py <tracking_links> <onsite_heading> <window>
<tracking_links> - a tracking link shape file that is produced by step3
<onsite_heading> -  a tracking link shape file that is same as the input tracking_links but add two newly calculated headings fields ("pazm2" and "pazm2")
<window> - the size of a search window that is used to for select those intersected links for an onsite-heading calculation, the default is 35 meters (close to a road width)

Example:
python step6_link_endpoint_onsite_heading.py ./mudanyuan/result/tracking_links1.shp ./mudanyuan/result/tracking_links2.shp 35

7. step7_link_line_density.py
Calculating line density at a fractile position of a tracking link. Here we computed three density values that are attributed to the start-point, middle-point and end-point of the link

Usage:
python step6_link_line_density.py 

Usage:
python step6_link_line_density.py 
usage: python step6_link_line_density.py <tracking_links> <line_density> <window>
<tracking_links> - a tracking link shape file with onsite_heading data, which is produced by step4
<line_density> - a tracking link shape file that is same as the input tracking_links but add three newly calculated line density fields ("ld", "pd1" and "pd2")
<window> - the size of a search window that is used to for select those intersected links for a line density calculation, the default is 35 meters (close to a road width)

Example:
python step7_link_line_density.py ./mudanyuan/result/tracking_links2.shp ./mudanyuan/result/tracking_links3.shp 35

8. step8_link_spatial_reasoning.py
Labelling a tracking link by our proposed spatial reasoning method. The links are separated into a number of types as described by our paper

Usage:
python step7_link_spatial_reasoning.py 
usage: python step7_link_spatial_reasoning.py <tracking_links> <labeled> <Tag> <Gamma>
<tracking_links> -  a tracking link shape file with all geometric and motion measures, which is finished at step5
<labeled> - a tracking link shape file that contains a newly calculated "label" field, and more information about the definition of label can be found in our paper
<Tag> - direction similarity,an angle threshold
<Gamma> - fractile line density similarity,an density threshold

Example:
python step8_link_spatial_reasoning.py ./mudanyuan/result/tracking_links3.shp ./mudanyuan/result/tracking_links4.shp 27 0.33
 