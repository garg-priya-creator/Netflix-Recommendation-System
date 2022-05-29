import math
from flask import Flask, render_template, request
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def prepare_data(x):
        return str.lower(x.replace(" ", ""))

def create_soup(x):
    return x['Genre'] + ' ' + x['Tags'] + ' ' +x['Actors']+' '+ x['ViewerRating']

def get_recommendations(title, cosine_sim):
    global result
    title=title.replace(' ','').lower()
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:51]
    movie_indices = [i[0] for i in sim_scores]
    result =  netflix_data.iloc[movie_indices]
    result.reset_index(inplace = True)
    return result

netflix_data = pd.read_csv('NetflixDataset.csv',encoding='latin-1', index_col = 'Title')
netflix_data.index = netflix_data.index.str.title()
netflix_data = netflix_data[~netflix_data.index.duplicated()]
netflix_data.rename(columns={'View Rating':'ViewerRating'}, inplace=True)
Language = netflix_data.Languages.str.get_dummies(',')
Lang = Language.columns.str.strip().values.tolist()
Lang = set(Lang)
Titles = set(netflix_data.index.to_list())

netflix_data['Genre'] = netflix_data['Genre'].astype('str')
netflix_data['Tags'] = netflix_data['Tags'].astype('str')
netflix_data['IMDb Score'] = netflix_data['IMDb Score'].apply(lambda x: 6.6 if math.isnan(x) else x)
netflix_data['Actors'] = netflix_data['Actors'].astype('str')
netflix_data['ViewerRating'] = netflix_data['ViewerRating'].astype('str')
new_features = ['Genre', 'Tags', 'Actors', 'ViewerRating']
selected_data = netflix_data[new_features]
for new_feature in new_features:
    selected_data.loc[:, new_feature] = selected_data.loc[:, new_feature].apply(prepare_data)
selected_data.index = selected_data.index.str.lower()
selected_data.index = selected_data.index.str.replace(" ",'')
selected_data['soup'] = selected_data.apply(create_soup, axis = 1)

count = CountVectorizer(stop_words='english')
count_matrix = count.fit_transform(selected_data['soup'])
cosine_sim2 = cosine_similarity(count_matrix, count_matrix)
selected_data.reset_index(inplace = True)
indices = pd.Series(selected_data.index, index=selected_data['Title'])
result = 0
df = pd.DataFrame()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', languages = Lang, titles = Titles) 

@app.route('/about',methods=['POST'])
def getvalue():
    global df
    movienames = request.form.getlist('titles')
    languages = request.form.getlist('languages')
    for moviename in movienames:
        get_recommendations(moviename,cosine_sim2)
        for language in languages:
            df = pd.concat([result[result['Languages'].str.count(language) > 0], df], ignore_index=True)
    df.drop_duplicates(keep = 'first', inplace = True)
    df.sort_values(by = 'IMDb Score', ascending = False, inplace = True)
    images = df['Image'].tolist()
    titles = df['Title'].tolist()
    return render_template('result.html',  titles =  titles, images = images)

@app.route('/moviepage/<name>')
def movie_details(name):
    global df
    details_list = df[df['Title'] == name].to_numpy().tolist()
    return render_template('moviepage.html', details = details_list[0])


if __name__ == '__main__':
    app.run(debug=False)
