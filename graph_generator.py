from pyvis.network import Network


def generate_graph(visited_tiles):
    net = Network(notebook=False, directed=True, height="750px", width="100%")
    # Load data directly from your scraper dict
    for parent, children in visited_tiles.items():
        if not children: continue
        net.add_node(parent, label=parent, color="#3b82f6")
        for child in children:
            net.add_node(child, label=child)
            net.add_edge(parent, child)

    # Turn on physics buttons so you can tweak layout on the fly
    template = net.templateEnv.get_template(net.path)
    net.template = template

    net.show_buttons(filter_=['physics'])
    net.show("wikipedia_graph.html", notebook=False)