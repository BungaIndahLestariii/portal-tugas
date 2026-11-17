import { handleUpload } from '@vercel/blob/client';

export default async function handler(request, response) {
  if (request.method !== 'POST') {
    return response.status(405).json({ error: 'Method tidak diizinkan' });
  }

  try {
    const body = typeof request.body === 'string' ? JSON.parse(request.body) : request.body;

    const jsonResponse = await handleUpload({
      body,
      request,
      onBeforeGenerateToken: async () => {
        return {
          // Tanpa batasan allowedContentTypes agar semua jenis file (PDF, Word, dll) diizinkan
          maximumSizeInBytes: 1024 * 1024 * 1024, // Maksimal 1 GB
          addRandomSuffix: true,
        };
      },
      onUploadCompleted: async ({ blob }) => {
        console.log('Upload selesai:', blob.url);
      },
    });

    return response.status(200).json(jsonResponse);
  } catch (error) {
    console.error('Blob upload error:', error);
    return response.status(400).json({ error: error.message });
  }
}
