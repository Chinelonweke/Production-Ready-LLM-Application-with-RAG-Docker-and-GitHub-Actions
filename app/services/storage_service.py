# app/services/storage_service.py
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import time
import os
from datetime import datetime
from config import Config
from logger_config import get_logger

class S3Storage:
    """Enhanced S3 Storage service with logging and error handling"""
    
    def __init__(self):
        self.logger = get_logger("s3_storage")
        self.s3 = None
        self.bucket = Config.AWS_BUCKET_NAME
        self._initialize_s3()
    
    def _initialize_s3(self):
        """Initialize S3 client with proper error handling"""
        try:
            self.logger.info("☁️  Initializing S3 storage service")
            start_time = time.time()
            
            # Check if credentials are available
            if not Config.AWS_ACCESS_KEY or not Config.AWS_SECRET_KEY:
                raise ValueError("AWS credentials not found in configuration")
            
            # Initialize S3 client
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=Config.AWS_ACCESS_KEY,
                aws_secret_access_key=Config.AWS_SECRET_KEY,
                region_name=Config.AWS_REGION
            )
            
            # Test connection
            self._test_connection()
            
            init_time = time.time() - start_time
            self.logger.info(f"✅ S3 storage service initialized successfully in {init_time:.2f}s")
            self.logger.info(f"🪣 Using bucket: {self.bucket}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize S3 storage: {str(e)}")
            raise
    
    def _test_connection(self):
        """Test S3 connection"""
        try:
            # List buckets to test connection
            response = self.s3.list_buckets()
            bucket_names = [bucket['Name'] for bucket in response['Buckets']]
            
            if self.bucket not in bucket_names:
                self.logger.warning(f"⚠️  Bucket '{self.bucket}' not found in available buckets: {bucket_names}")
            else:
                self.logger.info(f"✅ Bucket '{self.bucket}' verified")
                
        except Exception as e:
            self.logger.error(f"❌ S3 connection test failed: {str(e)}")
            raise
    
    def upload_file(self, file_obj, filename, folder="documents"):
        """
        Upload file to S3 with logging
        
        Args:
            file_obj: File object to upload
            filename (str): Name of the file
            folder (str): Folder/prefix in S3
        
        Returns:
            dict: Upload result with status and details
        """
        try:
            # Create full key with folder and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = f"{folder}/{timestamp}_{filename}"
            
            self.logger.info(f"📤 Uploading file: {filename} to {key}")
            start_time = time.time()
            
            # Get file size for logging
            file_obj.seek(0, 2)  # Seek to end
            file_size = file_obj.tell()
            file_obj.seek(0)  # Reset to beginning
            
            # Upload file
            self.s3.upload_fileobj(
                file_obj, 
                self.bucket, 
                key,
                ExtraArgs={
                    'ContentType': self._get_content_type(filename),
                    'Metadata': {
                        'original_name': filename,
                        'upload_timestamp': timestamp,
                        'file_size': str(file_size)
                    }
                }
            )
            
            upload_time = time.time() - start_time
            self.logger.info(f"✅ File uploaded successfully in {upload_time:.2f}s")
            self.logger.info(f"📊 File size: {self._format_file_size(file_size)}")
            
            return {
                "success": True,
                "key": key,
                "bucket": self.bucket,
                "size": file_size,
                "upload_time": upload_time,
                "url": f"s3://{self.bucket}/{key}"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            self.logger.error(f"❌ S3 upload failed with error code {error_code}: {str(e)}")
            return {
                "success": False,
                "error": f"S3 error: {error_code}",
                "details": str(e)
            }
        except Exception as e:
            self.logger.error(f"❌ File upload failed: {str(e)}")
            return {
                "success": False,
                "error": "Upload failed",
                "details": str(e)
            }
    
    def get_file(self, key):
        """
        Retrieve file from S3
        
        Args:
            key (str): S3 object key
        
        Returns:
            dict: File data and metadata
        """
        try:
            self.logger.info(f"📥 Downloading file: {key}")
            start_time = time.time()
            
            # Get object
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            
            download_time = time.time() - start_time
            file_size = response['ContentLength']
            
            self.logger.info(f"✅ File downloaded successfully in {download_time:.2f}s")
            self.logger.info(f"📊 File size: {self._format_file_size(file_size)}")
            
            return {
                "success": True,
                "body": response['Body'],
                "metadata": response.get('Metadata', {}),
                "content_type": response.get('ContentType', ''),
                "size": file_size,
                "download_time": download_time
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                self.logger.warning(f"⚠️  File not found: {key}")
            else:
                self.logger.error(f"❌ S3 download failed with error code {error_code}: {str(e)}")
            
            return {
                "success": False,
                "error": f"S3 error: {error_code}",
                "details": str(e)
            }
        except Exception as e:
            self.logger.error(f"❌ File download failed: {str(e)}")
            return {
                "success": False,
                "error": "Download failed",
                "details": str(e)
            }
    
    def list_files(self, folder="documents", limit=100):
        """
        List files in S3 bucket
        
        Args:
            folder (str): Folder/prefix to list
            limit (int): Maximum number of files to return
        
        Returns:
            dict: List of files with metadata
        """
        try:
            self.logger.info(f"📋 Listing files in folder: {folder}")
            
            response = self.s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=folder,
                MaxKeys=limit
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "etag": obj['ETag']
                    })
            
            self.logger.info(f"✅ Found {len(files)} files")
            
            return {
                "success": True,
                "files": files,
                "count": len(files)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list files: {str(e)}")
            return {
                "success": False,
                "error": "List operation failed",
                "details": str(e)
            }
    
    def delete_file(self, key):
        """
        Delete file from S3
        
        Args:
            key (str): S3 object key
        
        Returns:
            dict: Deletion result
        """
        try:
            self.logger.info(f"🗑️  Deleting file: {key}")
            
            self.s3.delete_object(Bucket=self.bucket, Key=key)
            
            self.logger.info(f"✅ File deleted successfully: {key}")
            
            return {
                "success": True,
                "key": key
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete file {key}: {str(e)}")
            return {
                "success": False,
                "error": "Delete operation failed",
                "details": str(e)
            }
    
    def _get_content_type(self, filename):
        """Get content type based on file extension"""
        extension = filename.lower().split('.')[-1]
        content_types = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'wav': 'audio/wav',
            'mp3': 'audio/mpeg',
            'flac': 'audio/flac',
            'ogg': 'audio/ogg'
        }
        return content_types.get(extension, 'application/octet-stream')
    
    def _format_file_size(self, size_bytes):
        """Format file size in human-readable format"""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f}{size_names[i]}"
    
    def health_check(self):
        """Perform a health check on S3 service"""
        try:
            # Try to list buckets
            self.s3.list_buckets()
            self.logger.info("✅ S3 storage health check passed")
            return True
        except Exception as e:
            self.logger.error(f"❌ S3 storage health check failed: {str(e)}")
            return False
    
    def get_storage_info(self):
        """Get storage service information"""
        return {
            "provider": "AWS S3",
            "bucket": self.bucket,
            "region": Config.AWS_REGION,
            "status": "active" if self.health_check() else "error"
        }