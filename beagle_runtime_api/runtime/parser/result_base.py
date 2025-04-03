class ResultBase():
    def __init__(self,category,tik,x,y) -> None:
        self.tik=tik
        self.x=x
        self.y=y
        self.cat=category
    
    def __str__(self) -> str:
        return f'[{self.cat}] tik={self.tik},coor=({self.x},{self.y})'