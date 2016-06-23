/* Open an image, returning the best version of that image for thumbnailing. 
 *
 * libjpeg supports fast shrink-on-read, so if we have a JPEG, we can ask 
 * VIPS to load a lower resolution version.
 */
static VipsImage *
thumbnail_open( VipsObject *process, const char *filename )
{
	const char *loader;
	VipsImage *im;

	vips_info( "vipsthumbnail", "thumbnailing %s", filename );

	if( linear_processing )
		vips_info( "vipsthumbnail", "linear mode" ); 

	if( !(loader = vips_foreign_find_load( filename )) )
		return( NULL );

	vips_info( "vipsthumbnail", "selected loader is %s", loader ); 

	if( strcmp( loader, "VipsForeignLoadJpegFile" ) == 0 ) {
		int jpegshrink;

		/* This will just read in the header and is quick.
		 */
		if( !(im = vips_image_new_from_file( filename, NULL )) )
			return( NULL );

		jpegshrink = thumbnail_find_jpegshrink( im );

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

		shrink = calculate_shrink( im ); 

		g_object_unref( im );

		vips_info( "vipsthumbnail", 
			"loading PDF/SVG with factor %g pre-shrink", 
			shrink ); 

		/* We can't use UNBUFERRED safely on very-many-core systems.
		 */
		if( !(im = vips_image_new_from_file( filename, 
			"access", VIPS_ACCESS_SEQUENTIAL,
			"scale", 1.0 / shrink,
			NULL )) )
			return( NULL );
	}
	else if( strcmp( loader, "VipsForeignLoadWebpFile" ) == 0 ) {
		double shrink;

		/* This will just read in the header and is quick.
		 */
		if( !(im = vips_image_new_from_file( filename, NULL )) )
			return( NULL );

		shrink = calculate_shrink( im ); 

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

	vips_object_local( process, im );

	return( im ); 
}
