import { useEffect, useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [message, setMessage] = useState('');
  const [health, setHealth] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Fetch data from backend
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get('http://127.0.0.1:8000/');
        setMessage(response.data.message);
        
        const healthResponse = await axios.get('http://127.0.0.1:8000/api/health');
        setHealth(healthResponse.data.status);
      } catch (error) {
        console.error('Error fetching data:', error);
        setMessage('Error connecting to backend');
        setHealth('unhealthy');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-100 to-white">
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center text-gray-800 mb-8">
          Next.js Frontend with FastAPI Backend
        </h1>
        
        <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-700">Backend Status:</h2>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                health === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {isLoading ? 'Checking...' : health}
              </span>
            </div>
            
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-700 mb-2">Message from Backend:</h3>
              <p className="text-gray-600 bg-gray-50 p-3 rounded-md">
                {isLoading ? 'Loading...' : message}
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 