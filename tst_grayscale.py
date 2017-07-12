import cv2

image = cv2.imread("/home/k0k1/movie_catalogue_pictures/full/51.jpg")
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

cv2.imwrite("dull.jpg", gray_image)


