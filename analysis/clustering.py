__author__ = 'jerry'


def cluster_players_offense(output_filename):

    all_players = players.find(timeout=False)
    writer = csv.writer(open(output_filename, 'w'))

    all_features = []

    for player in all_players:
        fn, ln = look_up_player_name(player['id'])
        print 'Generating features for {0} {1}'.format(fn, ln)

        features = player_ocluster_features(player['id'])
        writer.writerow(features)

def cluster_players_defense(output_filename):

    all_players = players.find(timeout=False)
    writer = csv.writer(open(output_filename, 'w'))

    all_features = []

    for player in all_players:
        fn, ln = look_up_player_name(player['id'])
        print 'Generating features for {0} {1}'.format(fn, ln)

        features = player_dcluster_features(player['id'])
        writer.writerow(features)

def compute_team_clusters(data_file, clusters=5, method='GMM', plot=False):

    data = pylab.genfromtxt(data_file, delimiter=',')
    ids = data[:, 0]
    team_features = data[:, 1:]
    scaled_features = StandardScaler().fit_transform(team_features)

    cluster_obj = None

    if method == 'GMM':

        gmm = GMM(n_components=clusters).fit(scaled_features)
        weights = gmm.weights_
        means = gmm.means_
        labels = gmm.predict(scaled_features)
        cluster_obj = gmm

    #print labels

    categories = {}

    for label in pylab.unique(labels):
        categories[label] = []

    for label, team_id in zip(labels, ids):
        city, name = look_up_team_name(int(team_id))
        categories[label].append((int(team_id), ' '.join((city, name))))

    if plot:
        norm = Normalize(min(labels), max(labels))
        cm = mpl.cm.jet

        mds = MDS(n_components=2)
        res = mds.fit(scaled_features)

        pos = res.embedding_
        offset_radius = 10
        cluster_thetas = pylab.linspace(0, 2 * pylab.pi, clusters + 1)[0:clusters]
        cluster_vectors = [(offset_radius * pylab.cos(theta), offset_radius * pylab.sin(theta)) for theta in cluster_thetas]
        team_names = [' '.join(look_up_team_name(team_id)) for team_id in ids]

        gs = gridspec.GridSpec(1, 1)
        #ax_legend = mpl.subplot(gs[0, 1])
        ax_main = mpl.subplot(gs[0, 0])

        for i, coords in enumerate(pos):
            label = labels[i]
            color = cm(norm(label))
            offset = cluster_vectors[label]
            ax_main.plot(coords[0] + offset[0], coords[1] + offset[1], color=color, marker='o', label=team_names[i])

        datacursor(formatter='{label}'.format)

        proxies = []
        texts = []
        for cat in categories:
            proxy_artist = Circle((0,0), 1, fc=cm(norm(cat)))
            text = ',\n '.join([team[1] for team in categories[cat]]) + '\n'
            proxies.append(proxy_artist)
            texts.append(text)

        ax_main.set_position([0.1, 0.1, 0.55, 0.75])
        ax_main.grid(True)
        ax_main.set_aspect('equal')
        ax_main.set_title('Team clusters')
        legend = ax_main.legend(proxies, texts, prop={'size': 'x-small'}, bbox_to_anchor=(1.5, 1.05))

        #ax_legend.add_artist(legend)

        mpl.show()

    return categories, cluster_obj

def compute_player_clusters(data_file, clusters=10, method='GMM', plot=False):

    data = pylab.genfromtxt(data_file, delimiter=',')
    ids = data[:, 0]
    player_features = data[:, 1:]

    non_empty_indices = pylab.where(pylab.any(player_features != 0, axis=1))

    non_empty_features = player_features[non_empty_indices]
    non_empty_ids = ids[non_empty_indices]
    scaled_features = StandardScaler().fit_transform(non_empty_features)

    #sims = euclidea_ndistances(non_empty_features)
    #print sims
    sims = player_feature_sim_matrix(non_empty_features)

    cluster_obj = None

    if method == 'Affinity':

        sims *= -1
        #af = AffinityPropagation(preference=-2000).fit(non_empty_features)
        af = AffinityPropagation(preference=-2000, affinity='precomputed').fit(sims)
        labels = af.labels_
        cluster_obj = af

    if method == 'KMeans':

        km = KMeans(n_clusters=clusters).fit(non_empty_features)
        labels = km.labels_
        cluster_obj = km

    if method == 'DBSCAN':

        sims = 1 - (sims / np.max(sims))
        db = DBSCAN(eps=0.75).fit(sims)
        labels = db.labels_
        cluster_obj = db

    if method == 'Ward':

        ward = Ward(n_clusters=clusters).fit(sims)
        labels = ward.labels_
        cluster_obj = ward

    if method == 'GMM':

        gmm = GMM(n_components=clusters).fit(scaled_features)
        weights = gmm.weights_
        means = gmm.means_
        labels = gmm.predict(scaled_features)
        cluster_obj = gmm

        #print weights
        #print means

    #print labels

    if plot:
        norm = Normalize(min(labels), max(labels))
        cm = mpl.cm.jet

        mds = MDS(n_components=2)
        res = mds.fit(scaled_features)

        pos = res.embedding_
        offset_radius = 10
        cluster_thetas = pylab.linspace(0, 2 * pylab.pi, clusters + 1)[0:clusters]
        cluster_vectors = [(offset_radius * pylab.cos(theta), offset_radius * pylab.sin(theta)) for theta in cluster_thetas]
        player_names = [' '.join(look_up_player_name(player_id)) for player_id in non_empty_ids]

        for i, coords in enumerate(pos):
            label = labels[i]
            player_id = non_empty_ids[i]
            color = cm(norm(label))
            offset = cluster_vectors[label]
            mpl.plot(coords[0] + offset[0], coords[1] + offset[1], color=color, marker='o', label=player_names[i])

        datacursor(formatter='{label}'.format)

        mpl.show()

    categories = {}

    for label in pylab.unique(labels):
        categories[label] = []

    for label, player_id in zip(labels, non_empty_ids):
        fn, ln = look_up_player_name(int(player_id))
        categories[label].append((int(player_id), ' '.join((fn, ln))))

    return categories, cluster_obj

def find_member_in_clusters(clusters, member):

    for cluster in clusters:
        for p in clusters[cluster]:
            if type(member) == str:
                if p[1] == member:
                    return cluster
            if type(member) == int:
                if p[0] == member:
                    return cluster

    return None

def cluster_overlap(c1, c2):

    overlap = [p1 for p1 in c1 if p1 in c2]

    return overlap
