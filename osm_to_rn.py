import networkx as nx
import osmium as o
from osgeo import ogr
import argparse


class OSM2RNHandler(o.SimpleHandler):

    def __init__(self, rn):
        super(OSM2RNHandler, self).__init__()
        self.candi_highway_types = {'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified',
                                    'residential', 'motorway_link', 'trunk_link', 'primary_link', 'secondary_link',
                                    'tertiary_link'}
        self.rn = rn
        self.eid = 0

    def way(self, w):
        if 'highway' in w.tags and w.tags['highway'] in self.candi_highway_types:
            raw_eid = w.id
            coords = []
            for n in w.nodes:
                coords.append((n.lat, n.lon))
            if 'oneway' in w.tags:
                if w.tags['oneway'] != 'yes':
                    coords.reverse()
                edge_attr = {'eid': self.eid, 'coords': coords, 'raw_eid': raw_eid, 'highway': w.tags['highway']}
                rn.add_edge((coords[0][1], coords[0][0]),
                            (coords[-1][1], coords[-1][0]), **edge_attr)
                self.eid += 1
            else:
                # add edges for both directions
                edge_attr = {'eid': self.eid, 'coords': coords, 'raw_eid': raw_eid, 'highway': w.tags['highway']}
                rn.add_edge((coords[0][1], coords[0][0]),
                            (coords[-1][1], coords[-1][0]), **edge_attr)
                self.eid += 1

                reversed_coords = coords.copy()
                reversed_coords.reverse()
                edge_attr = {'eid': self.eid, 'coords': reversed_coords, 'raw_eid': raw_eid, 'highway': w.tags['highway']}
                rn.add_edge((reversed_coords[0][1], reversed_coords[0][0]),
                            (reversed_coords[-1][1], reversed_coords[-1][0]), **edge_attr)
                self.eid += 1


def store_shp(rn, target_path):
    ''' nodes: [lng, lat] '''
    rn.remove_nodes_from(list(nx.isolates(rn)))
    print('# of nodes:{}'.format(rn.number_of_nodes()))
    print('# of edges:{}'.format(rn.number_of_edges()))
    for _, _, data in rn.edges(data=True):
        geo_line = ogr.Geometry(ogr.wkbLineString)
        for coord in data['coords']:
            geo_line.AddPoint(coord[1], coord[0])
        data['Wkb'] = geo_line.ExportToWkb()
        del data['coords']
    nx.write_shp(rn, target_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', help='the input path of the original osm data')
    parser.add_argument('--output_path', help='the output directory of the constructed road network')
    opt = parser.parse_args()
    print(opt)

    rn = nx.DiGraph()
    handler = OSM2RNHandler(rn)
    handler.apply_file(opt.input_path, locations=True)
    store_shp(rn, opt.output_path)
