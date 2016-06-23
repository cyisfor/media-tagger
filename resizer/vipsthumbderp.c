/* Calculate the shrink factor, taking into account auto-rotate, the fit mode,
 * and so on.
 */
static double
calculate_shrink( VipsImage *im, int target_width)
{
	// Xsize divided by this should equal target_width
	return ((double) im->Xsize) / target_width;
}

/* Find the best jpeg preload shrink.
 */
static int
thumbnail_find_jpegshrink( VipsImage *im, int target_width)
{
	/* Shrink-on-load is a simple block shrink and will add quite a bit of
	 * extra sharpness to the image. We want to block shrink to a
	 * bit above our target, then vips_resize() to the final size. 
	 *
	 * Leave at least a factor of two for the final resize step.
	 */

	double shrink = calculate_shrink(im, target_width);
	if( shrink >= 16 )
		return( 8 );
	else if( shrink >= 8 )
		return( 4 );
	else if( shrink >= 4 )
		return( 2 );
	else 
		return( 1 );
}


/* Open an image, returning the best version of that image for thumbnailing. 
 *
 * libjpeg supports fast shrink-on-read, so if we have a JPEG, we can ask 
 * VIPS to load a lower resolution version.
 */
static VipsImage *
thumbnail_open( const char *filename, bool* was_jpeg, int target_width)
{
	const char *loader;
	VipsImage *im;

	vips_info( "vipsthumbnail", "thumbnailing %s", filename );

	if( !(loader = vips_foreign_find_load( filename )) )
		return( NULL );

	vips_info( "vipsthumbnail", "selected loader is %s", loader ); 

	if( strcmp( loader, "VipsForeignLoadJpegFile" ) == 0 ) {
		*was_jpeg = true;
		int jpegshrink;

		/* This will just read in the header and is quick.
		 */
		if( !(im = vips_image_new_from_file( filename, NULL )) )
			return( NULL );

		jpegshrink = thumbnail_find_jpegshrink( im, target_width );

		g_object_unref( im );

		vips_info( "vipsthumbnail", 
			"loading jpeg with factor %d pre-shrink", 
			jpegshrink ); 

		/* We can't use UNBUFERRED safely on very-many-core systems.
		 */
		if( !(im = vips_image_new_from_file( filename, 
			"access", VIPS_ACCESS_SEQUENTIAL,
			"shrink", jpegshrink,
			NULL )) )
			return( NULL );
	}
	else if( strcmp( loader, "VipsForeignLoadPdfFile" ) == 0 ||
		strcmp( loader, "VipsForeignLoadSvgFile" ) == 0 ) {
		double shrink;

		/* This will just read in the header and is quick.
		 */
		if( !(im = vips_image_new_from_file( filename, NULL )) )
			return( NULL );

		g_object_unref( im );

		shrink = calculate_shrink(im,target_width);

		vips_info( "vipsthumbnail", 
			"loading PDF/SVG with factor %g pre-shrink", 
			shrink ); 

		/* We can't use UNBUFERRED safely on very-many-core systems.
		 */
		if( !(im = vips_image_new_from_file( filename, 
			"access", VIPS_ACCESS_SEQUENTIAL,
			"scale", 1.0 / target_width,
			NULL )) )
			return( NULL );
	}
	else if( strcmp( loader, "VipsForeignLoadWebpFile" ) == 0 ) {
		double shrink;

		/* This will just read in the header and is quick.
		 */
		if( !(im = vips_image_new_from_file( filename, NULL )) )
			return( NULL );

		shrink = calculate_shrink(im, target_shrink);

		g_object_unref( im );

		vips_info( "vipsthumbnail", 
			"loading webp with factor %g pre-shrink", 
			shrink ); 

		/* We can't use UNBUFERRED safely on very-many-core systems.
		 */
		if( !(im = vips_image_new_from_file( filename, 
			"access", VIPS_ACCESS_SEQUENTIAL,
			"shrink", (int) shrink,
			NULL )) )
			return( NULL );
	}
	else {
		/* All other formats. We can't use UNBUFERRED safely on 
		 * very-many-core systems.
		 */
		if( !(im = vips_image_new_from_file( filename, 
			"access", VIPS_ACCESS_SEQUENTIAL,
			NULL )) )
			return( NULL );
	}

	return( im ); 
}
