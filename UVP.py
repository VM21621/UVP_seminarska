import requests
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

API_KEY = "797dacab93a96c4a7e0ab91052873c8c"
BASE_URL = "https://api.themoviedb.org/3"
JSONFILE = "movies.json"

def load():
    try:
        with open(JSONFILE, "r", encoding="utf-8") as f:
            content=f.read()
            if len(content)!=0:
                 return json.loads(content)
            else:
                return {"last_page": 0, "movies": {}}
    except FileNotFoundError:
        return {"last_page": 0, "movies": {}}



def savepages(data):
    with open(JSONFILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main_fetch(loadpages=5):
    data = load()
    last_page = data["last_page"]
    moviesseznam = data["movies"]

    for page in range(last_page + 1, last_page + loadpages + 1):
        url = f"{BASE_URL}/movie/popular"
        params = {"api_key": API_KEY, "language": "en-US", "page": page}
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Error fetching page {page}")
            continue

        url2 = f"{BASE_URL}/genre/movie/list"
        params2 = {"api_key": API_KEY, "language": "en-US"}
        response2 = requests.get(url2, params=params2)
        if response2.status_code != 200:
            genremap={}
        else: 
            genremap={genre["id"]: genre["name"] for genre in response2.json().get("genres", [])}
        movies = response.json().get("results", [])
        
        for movie in movies:
            title = movie.get("title")
            genre_ids = movie.get("genre_ids", [])
            genres = [genremap.get(gid, "Unknown") for gid in genre_ids]

            moviesseznam[title] = {
                    "genres": genres,
                    "release_date": movie.get("release_date"),
                    "vote_average": movie.get("vote_average"),
                    "vote_count": movie.get("vote_count"),
                    "synopsis": movie.get("overview")
                }
    if loadpages!="":
        data["last_page"] = last_page + loadpages
        data["movies"] = moviesseznam
        savepages(data)
    return moviesseznam

def datefilter(date, mini, maxi):
    try:
        movie_date = datetime.strptime(date, "%Y-%m-%d")
        min_date = datetime.strptime(mini, "%d.%m.%Y")
        max_date = datetime.strptime(maxi, "%d.%m.%Y")
    except:
        return False
    return min_date < movie_date < max_date

 
def checkforfilter(filterlist, data):#filterlist = [genrelist,genrenonlist,timerange,rating,totalrates]
    genres=data["genres"]
    date=data["release_date"]
    rating=data["vote_average"]
    totalvotes=data["vote_count"]
    for neededgenre in filterlist[0]:
        if neededgenre not in genres:
            return False
    for badgenre in filterlist[1]:
        if badgenre in genres:
            return False
    
    if rating<float(filterlist[3]) or totalvotes<float(filterlist[4]):
        return False
    return    datefilter(date,filterlist[2][0],filterlist[2][1])
       
       #just if the user inputs a non existant genre

def existantgenres():#just if the user inputs a non existant genre
    url2 = f"{BASE_URL}/genre/movie/list"
    params = {"api_key": API_KEY, "language": "en-US"}
    response = requests.get(url2, params=params)
    if response.status_code != 200:
        return None
    return [genre["name"] for genre in response.json().get("genres", [])]

def filter(filterlist,seznam):
    seznammain={}
    for movie in seznam:
        data=seznam[movie]
        if checkforfilter(filterlist,data):
            seznammain[movie]=seznam[movie]
    return seznammain

def findrecommendation(movieseznam,description):
    description=description.lower().split()
    for word in description:
        if len(word)>5:
            description.append(word[:4]) #for longer words we can search for their prepone
    deletewords={"the", "is", "are", "of", "and", "to", "an", "a"}
    description=[word for word in description if word not in deletewords]
    moviepoints=[]
    for title in movieseznam:
        synopsis=movieseznam[title]["synopsis"].lower()
        points=0
        for word in description:
            if word in synopsis: #counts if there is a word with a word e.g. teen-> teenager
                points+=1
        moviepoints.append([
                            title,
                            points, 
                            movieseznam[title]["release_date"],
                            movieseznam[title]["vote_average"],
                            movieseznam[title]["genres"],            
                            synopsis])
    df = pd.DataFrame(moviepoints, columns=["title","points","release_date", "rating", "genres", "synopsis"])
    df = df.sort_values(by=["points", "rating"], ascending=[False, False])
    return  df

def main():      
    a=int(input("How many pages should we load?(1page=20movies)"))
    movieseznam=main_fetch(a)
    print(f"Collected {len(movieseznam)} movies in total")
    genrelist=existantgenres()
    if input("customize your filters?:(input yes or no)")=="yes":
        genreneeded=[]
        genrenon=[]
        while True:
            inp=input("Do you want any more specific genres(when you are done input 'No'): ")
            if inp=="No":
                break
            if inp not in genrelist:
                print("genre doesnt exist exemple: Action ")
                
            else:
                genreneeded.append(inp)
        while True:
            inp=input("Do you want to remove all of a certain genre(when you are done input 'No'): ")
            if inp=="No":
                break
            if inp not in genrelist:
                print("genre doesnt exist exemple: Horror ")
            elif inp in genreneeded:
                print("You want to see a movie with and without "+str(inp)+"? i dont think that makes sense..")
            else:
                genrenon.append(inp)
        datemin=input("write the earliest possible release date for your movie(day.month.year): ")
        datemax=input("write the latest possible release date for your movie(day.month.year): ")
        minscore=input("Minimum rating?")
        mincount=input("Minimum number of voters?")

        if int(datemin.split(".")[len(datemin.split("."))-1])<1000:
            datemin="1.1.1000"
        testlistforfilter=[genreneeded,genrenon,[datemin,datemax],minscore,mincount]

        jsonseznam = load()
        jsonseznam["testlistforfilter"] = testlistforfilter
        savepages(jsonseznam)
    else:
        try:
            with open (JSONFILE, encoding="utf-8") as f:
               testlistforfilter = json.load(f)["testlistforfilter"]
        except:
            testlistforfilter=[[],[],["1.1.1000","1.1.3000"],0,0]#it means the person has never used this b4 and also doesnt want to add any filters


    mainseznam = filter(testlistforfilter, movieseznam)
    if len(mainseznam)==0:
        print("No such movie was collected")
        return None

    description=input("Write a further description of the movie, keywords: ")    
    #end of inputs

    df = findrecommendation(mainseznam, description)
    topgraph =df.head(10)
    topoptions = df.head(10)[["title", "release_date", "rating", "genres", "synopsis"]]
    topoptions["genres"] = [", ".join(genres) for genres in topoptions["genres"]]
    for _, movie in topoptions.iterrows():
        print("-" * 80)
        print(f"Title       : {movie['title']}")
        print(f"Release Date: {movie['release_date']}")
        print(f"Rating      : {movie['rating']}")
        print(f"Genres      : {movie['genres']}")
        print(f"Synopsis    : {movie['synopsis']}\n")
        

    plt.figure(figsize=(9, 5))
    plt.bar(topgraph["title"], topgraph["points"], label="Similarity to description",alpha=0.6)
    plt.plot(topgraph["title"], topgraph["rating"], color="red", marker="o", label="Rating")
    
    plt.xlabel("Movie Title")
    plt.ylabel("Score & Rating")
    plt.title("Recommendations")
    plt.xticks(rotation=30, ha="right")
    plt.legend()
    plt.show()




if __name__ == "__main__":
    main()



