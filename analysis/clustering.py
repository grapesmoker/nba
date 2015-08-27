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

def cluster_teams_offense(output_filename):

    all_teams = teams.find(timeout=False)
    writer = csv.writer(open(output_filename, 'w'))

    all_features = []

    for team in all_teams:
        print 'Generating features for {0} {1}'.format(team['city'], team['name'])

        features = team_ocluster_features(team['id'])
        writer.writerow(features)

def cluster_teams_defense(output_filename):

    all_teams = teams.find(timeout=False)
    writer = csv.writer(open(output_filename, 'w'))

    all_features = []

    for team in all_teams:
        print 'Generating features for {0} {1}'.format(team['city'], team['name'])

        features = team_dcluster_features(team['id'])
        writer.writerow(features)

def compare_players_offense(p1, p2, weights=None):

    if type(p1) == str and type(p2) == str:
        fn1, ln1 = p1.split()
        fn2, ln2 = p2.split()

        p1_id = int(look_up_player_id(fn1, ln1))
        p2_id = int(look_up_player_id(fn2, ln2))

    elif type(p1) == int and type(p2) == int:
        p1_id = p1
        p2_id = p2

        fn1, ln1 = look_up_player_name(p1_id)
        fn2, ln2 = look_up_player_name(p2_id)

    else:
        return None

    p1_f = player_ocluster_features(p1_id)
    p2_f = player_ocluster_features(p2_id)

    sim = player_feature_sim(p1_f, p2_f, weights)
    dist = euclidean(p1_f[1:], p2_f[1:])

    print '{:25}{:>10}{:>10}{:>10}{:>10}{:>10}{:>10}'.format('Player', 'AST%', 'TS%', 'ORB%', 'USG%', 'ORTG%', 'MP%')
    print '{:->85}'.format('')
    print '{:25}{:10.3}{:10.3}{:10.3}{:10.3}{:10.3f}{:10.3}'.format(' '.join((fn1, ln1)), p1_f[1], p1_f[2], p1_f[3], p1_f[4], p1_f[5], p1_f[6])
    print '{:25}{:10.3}{:10.3}{:10.3}{:10.3}{:10.3f}{:10.3}'.format(' '.join((fn2, ln2)), p2_f[1], p2_f[2], p2_f[3], p2_f[4], p2_f[5], p2_f[6])
    #print '{:->85}'.format('')
    #print '{:25}{:10.3}'.format('Euclidean distance:', dist)

def compare_players_defense(p1, p2, weights=None):

    if type(p1) == str and type(p2) == str:
        fn1, ln1 = p1.split()
        fn2, ln2 = p2.split()

        p1_id = int(look_up_player_id(fn1, ln1))
        p2_id = int(look_up_player_id(fn2, ln2))

    elif type(p1) == int and type(p2) == int:
        p1_id = p1
        p2_id = p2

        fn1, ln1 = look_up_player_name(p1_id)
        fn2, ln2 = look_up_player_name(p2_id)

    else:
        return None

    p1_f = player_dcluster_features(p1_id)
    p2_f = player_dcluster_features(p2_id)

    sim = player_feature_sim(p1_f, p2_f, weights)
    dist = euclidean(p1_f[1:], p2_f[1:])

    print '{:25}{:>10}{:>10}{:>10}{:>10}{:>10}{:>10}'.format('Player', 'BLK%', 'STL%', 'DRB%', 'DRTG', 'PF%', 'MP%')
    print '{:->85}'.format('')
    print '{:25}{:10.3}{:10.3}{:10.3}{:10.3f}{:10.3f}{:10.3}'.format(' '.join((fn1, ln1)), p1_f[1], p1_f[2], p1_f[3], p1_f[4], p1_f[5], p1_f[6])
    print '{:25}{:10.3}{:10.3}{:10.3}{:10.3f}{:10.3f}{:10.3}'.format(' '.join((fn2, ln2)), p2_f[1], p2_f[2], p2_f[3], p2_f[4], p2_f[5], p2_f[6])
    #print '{:->85}'.format('')
    #print '{:25}{:10.3}'.format('Euclidean distance:', dist)

def player_feature_sim(p1, p2, weights=None):

    if p1[0] > 1000:
        p1 = p1[1:]
    if p2[0] > 1000:
        p2 = p2[1:]

    if weights is None:
        weights = pylab.ones(len(p1))

    s = pylab.array([w * ((abs(x - y) / abs(x + y)))**2 for x, y, w in zip(p1, p2, weights)])
    #s = pylab.array([w * (x + y) / (x * y) for x, y, w in zip(p1, p2, weights)])

    d = pylab.sqrt(pylab.sum(s))

    if pylab.isnan(d):
        d = 0

    return d

def player_feature_sim_matrix(feature_matrix, feature_weights=None):

    shape = feature_matrix.shape
    sims = pylab.zeros((shape[0], shape[0]))

    for i, p1 in enumerate(feature_matrix):
        for j, p2 in enumerate(feature_matrix):
            sims[i][j] = player_feature_sim(p1, p2, weights=None)

    return sims


# for i in range(len(test_subset)):
#     team1 = test_subset[i]['home_team']
#     team2 = test_subset[i]['away_team']
#     margin = test_subset[i]['home_points'] - test_subset[i]['away_points']
#     pred_margin = test_pred[i]
#     line = test_line[i]
#     t1_name = ' '.join(nba.look_up_team_name(team1))
#     t2_name = ' '.join(nba.look_up_team_name(team2))
#     if line > 0:
#         # home are favored
#         if pred_margin > line:
#             # I have bet on home
#             if line > margin:
#                 status = 'lose'
#             if line < margin:
#                 status = 'win'
#             if line == margin:
#                 status = 'tie'
#         if pred_margin < line:
#             # I have bet on away
#             if line > margin:
#                 status = 'win'
#             if line < margin:
#                 status = 'lose'
#             if line == margin:
#                 status = 'tie'
#     if line < 0:
#         # away are favored
#         if pred_margin < line:
#             # I have bet on away
#             if line < margin:
#                 status = 'lose'
#             if line > margin:
#                 status = 'win'
#             if line == margin:
#                 status = 'tie'
#         if pred_margin > line:
#             # I have bet on home
#             if line < margin:
#                 status = 'win'
#             if line > margin:
#                 status = 'lose'
#             if line == margin:
#                 status = 'tie'
#     print '{:50} {:>15} {:>25} {:>15} {:>15}'.format(' vs '.join((t1_name, t2_name)), 'line: {: 2.1f}'.format(line), 'predicted: {: 2.1f}'.format(pred_margin), 'actual: {: 2.1f}'.format(margin), status)

