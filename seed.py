from app import app, db, Game
with app.app_context():
    db.create_all()
    if Game.query.count() == 0:
        db.session.add_all([
            Game(title="Minecraft", developer="Mojang", release_year=2011,
                 description="Um sandbox de construção e exploração.", cover="https://images.igdb.com/igdb/image/upload/t_cover_big/co49x5.jpg"),
            Game(title="Hollow Knight", developer="Team Cherry", release_year=2017,
                 description="Metroidvania de exploração em um reino subterrâneo.", cover="https://images.igdb.com/igdb/image/upload/t_cover_big/co93s2.jpg"),
            Game(title="Elden Ring", developer="FromSoftware", release_year=2022,
                 description="RPG de ação em um enorme mundo aberto.", cover="https://images.igdb.com/igdb/image/upload/t_cover_big/co4jni.jpg")
        ])
        db.session.commit()
        print("Jogos de exemplo inseridos.")
