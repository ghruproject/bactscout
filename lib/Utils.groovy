/*
 * Utility functions for GHRU ReadQC pipeline
 */

class Utils {
    
    /*
     * Check if Sylph database exists in specified directory or as a file
     * Returns the database path or null if not found
     */
    public static String checkSylphDatabase(String db_path) {
        if (!db_path) {
            return null
        }
        
        def db_file = new File(db_path)
        
        // If it's a direct file path and exists
        if (db_file.isFile() && db_file.exists()) {
            return db_path
        }
        
        // If it's a directory, look for .syldb files
        if (db_file.isDirectory()) {
            def syldb_files = db_file.listFiles({ file -> 
                file.getName().endsWith('.syldb') 
            } as FileFilter)
            
            if (syldb_files && syldb_files.length > 0) {
                return syldb_files[0].getAbsolutePath()
            }
        }
        
        return null
    }
}