import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const ChatPanel = ({ isMinimized = false, onToggleMinimize }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const pollIntervalRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input when panel is expanded
  useEffect(() => {
    if (!isMinimized && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isMinimized]);

  // Fetch messages on component mount
  useEffect(() => {
    fetchMessages();

    // Set up polling for new messages every 5 seconds
    pollIntervalRef.current = setInterval(fetchMessages, 5000);

    // Cleanup polling on unmount
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const fetchMessages = async () => {
    try {
      const response = await axios.get('/api/chat/messages');
      setMessages(response.data.messages);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch messages:', err);
      setError('Failed to load messages');
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();

    if (!newMessage.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      await axios.post('/api/chat/messages', {
        message: newMessage.trim()
      });

      setNewMessage('');
      // Fetch messages immediately to show the new message
      await fetchMessages();
    } catch (err) {
      console.error('Failed to send message:', err);
      if (err.response?.status === 429) {
        setError('Rate limit exceeded. Please wait before sending another message.');
      } else {
        setError('Failed to send message');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getMessageStyle = (isSystem) => {
    return isSystem
      ? 'bg-yellow-900/20 border-l-4 border-yellow-500 text-yellow-200'
      : 'bg-gray-700/50 hover:bg-gray-700/70';
  };

  const getUsernameStyle = (isSystem) => {
    return isSystem
      ? 'text-yellow-400 font-semibold'
      : 'text-blue-400 font-medium';
  };

  if (isMinimized) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={onToggleMinimize}
          className="bg-space-dark border border-gray-600 rounded-lg p-3 hover:bg-gray-700 transition-colors"
          title="Open Chat"
        >
          <div className="flex items-center space-x-2">
            <span className="text-xl">💬</span>
            <span className="text-sm font-medium">Chat</span>
            {messages.length > 0 && (
              <span className="bg-red-500 text-white text-xs rounded-full px-2 py-1">
                {messages.length}
              </span>
            )}
          </div>
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 h-96 bg-space-dark border border-gray-600 rounded-lg shadow-xl z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-600 bg-gray-800/50 rounded-t-lg">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <span className="mr-2">💬</span>
          Global Chat
        </h3>
        <button
          onClick={onToggleMinimize}
          className="text-gray-400 hover:text-white transition-colors"
          title="Minimize Chat"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {error && (
          <div className="bg-red-900/20 border border-red-500 text-red-200 p-2 rounded text-sm">
            {error}
          </div>
        )}

        {messages.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <span className="text-2xl mb-2 block">💭</span>
            No messages yet. Be the first to say hello!
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`p-2 rounded-lg ${getMessageStyle(message.is_system)}`}
            >
              <div className="flex items-center space-x-2 mb-1">
                <span className={getUsernameStyle(message.is_system)}>
                  {message.username}
                </span>
                <span className="text-xs text-gray-400">
                  {formatTimestamp(message.timestamp)}
                </span>
              </div>
              <p className="text-sm text-gray-200 break-words">
                {message.message}
              </p>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={sendMessage} className="p-3 border-t border-gray-600 bg-gray-800/50 rounded-b-lg">
        <div className="flex space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            maxLength={500}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !newMessage.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg transition-colors flex items-center"
          >
            {isLoading ? (
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>
        <div className="text-xs text-gray-400 mt-1">
          {newMessage.length}/500 characters
        </div>
      </form>
    </div>
  );
};

export default ChatPanel;
