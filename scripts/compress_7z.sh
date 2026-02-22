for X in $(ls | grep .tif);
do
  7z a -t7z -mx9 $X.7z $X >> ~/Desktop/7z.log
done
