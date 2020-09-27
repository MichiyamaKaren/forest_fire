from forest_fire import Forest


outdir = 'fire_out'
forest = Forest(N=50, p=0.3, f=6e-5)
result = forest.run_simulation(Nrounds=200, outdir=outdir)
result.generate_gif(outdir, njobs=8)
