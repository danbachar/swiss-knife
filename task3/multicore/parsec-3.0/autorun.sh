source ./env.sh

programs=(blackscholes  bodytrack  facesim  ferret  fluidanimate  freqmine  raytrace  swaptions  vips x264)

for program in "${programs[@]}"; do   # The quotes are necessary here
	cmd="parsecmgmt -a build -p $program -c gcc"
	eval "${cmd}"
	cmd="parsecmgmt -a build -p $program -c gcc-serial"
	eval "${cmd}"
done
