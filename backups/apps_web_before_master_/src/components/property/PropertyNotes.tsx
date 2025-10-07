import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  StickyNote,
  Plus,
  Edit3,
  Save,
  X,
  Trash2,
  Calendar,
  Clock,
  ChevronDown,
  ChevronUp,
  User,
  AlertCircle,
  FileText,
  TrendingUp,
  Scale,
  Search,
  Eye,
  Lock,
  MessageSquare,
  Filter
} from 'lucide-react';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/hooks/use-auth';

export interface PropertyNote {
  id: string;
  parcel_id: string;
  user_id: string;
  title: string;
  content: string;
  note_type: 'general' | 'investment' | 'legal' | 'inspection' | 'research';
  priority: 'low' | 'medium' | 'high';
  is_private: boolean;
  created_at: string;
  updated_at: string;
  created_by_name?: string;
}

interface PropertyNotesProps {
  parcelId: string;
  propertyAddress?: string;
}

export function PropertyNotes({ parcelId, propertyAddress }: PropertyNotesProps) {
  // Auth handling
  let user = null;
  try {
    const auth = useAuth();
    user = auth?.user || null;
  } catch (error) {
    console.log('Auth not available, using default user');
  }

  const [notes, setNotes] = useState<PropertyNote[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAddingNote, setIsAddingNote] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [expandedNotes, setExpandedNotes] = useState<Set<string>>(new Set());
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // New note form state
  const [newNote, setNewNote] = useState({
    title: '',
    content: '',
    note_type: 'general' as const,
    priority: 'medium' as const,
    is_private: false
  });

  // Edit note form state
  const [editingNote, setEditingNote] = useState<Partial<PropertyNote>>({});

  // Fetch notes on component mount
  useEffect(() => {
    fetchNotes();
  }, [parcelId]);

  const fetchNotes = async () => {
    if (!parcelId) return;

    setLoading(true);
    setError(null);

    try {
      const { data, error } = await supabase
        .from('property_notes')
        .select(`
          *,
          profiles:user_id (
            full_name,
            email
          )
        `)
        .eq('parcel_id', parcelId)
        .order('created_at', { ascending: false });

      if (error) {
        console.error('Error fetching notes:', error);
        setError('Unable to load notes. Please try again.');
        setNotes([]);
      } else {
        // Map the data to include created_by_name
        const notesWithUsernames = (data || []).map(note => ({
          ...note,
          created_by_name: note.profiles?.full_name || note.profiles?.email || 'User'
        }));
        setNotes(notesWithUsernames);
      }
    } catch (error: any) {
      console.error('Error fetching notes:', error);
      setError('Unable to load notes. Please try again.');
      setNotes([]);
    } finally {
      setLoading(false);
    }
  };

  const createNote = async () => {
    if (!newNote.title.trim() || !newNote.content.trim()) {
      setError('Please fill in both title and content');
      return;
    }

    try {
      const { data, error } = await supabase
        .from('property_notes')
        .insert({
          parcel_id: parcelId,
          user_id: user?.id || 'default-user',
          title: newNote.title.trim(),
          content: newNote.content.trim(),
          note_type: newNote.note_type,
          priority: newNote.priority,
          is_private: newNote.is_private
        })
        .select(`
          *,
          profiles:user_id (
            full_name,
            email
          )
        `)
        .single();

      if (error) {
        console.error('Error creating note:', error);
        setError('Unable to save note. Please try again.');
      } else {
        const noteWithUsername = {
          ...data,
          created_by_name: data.profiles?.full_name || data.profiles?.email || 'User'
        };

        setNotes([noteWithUsername, ...notes]);
        setNewNote({
          title: '',
          content: '',
          note_type: 'general',
          priority: 'medium',
          is_private: false
        });
        setIsAddingNote(false);
        setError(null);
      }
    } catch (error: any) {
      console.error('Error creating note:', error);
      setError('Unable to save note. Please try again.');
    }
  };

  const updateNote = async (noteId: string) => {
    if (!editingNote.title?.trim() || !editingNote.content?.trim()) {
      setError('Please fill in both title and content');
      return;
    }

    try {
      const { data, error } = await supabase
        .from('property_notes')
        .update({
          title: editingNote.title.trim(),
          content: editingNote.content.trim(),
          note_type: editingNote.note_type,
          priority: editingNote.priority,
          is_private: editingNote.is_private,
          updated_at: new Date().toISOString()
        })
        .eq('id', noteId)
        .select(`
          *,
          profiles:user_id (
            full_name,
            email
          )
        `)
        .single();

      if (error) {
        console.error('Error updating note:', error);
        setError('Unable to update note. Please try again.');
      } else {
        const updatedNoteWithUsername = {
          ...data,
          created_by_name: data.profiles?.full_name || data.profiles?.email || 'User'
        };

        setNotes(notes.map(note =>
          note.id === noteId ? updatedNoteWithUsername : note
        ));
        setEditingNoteId(null);
        setEditingNote({});
        setError(null);
      }
    } catch (error: any) {
      console.error('Error updating note:', error);
      setError('Unable to update note. Please try again.');
    }
  };

  const deleteNote = async (noteId: string) => {
    if (!confirm('Are you sure you want to delete this note?')) return;

    try {
      const { error } = await supabase
        .from('property_notes')
        .delete()
        .eq('id', noteId);

      if (error) {
        console.error('Error deleting note:', error);
        setError('Unable to delete note. Please try again.');
      } else {
        setNotes(notes.filter(note => note.id !== noteId));
      }
    } catch (error: any) {
      console.error('Error deleting note:', error);
      setError('Unable to delete note. Please try again.');
    }
  };

  const startEditingNote = (note: PropertyNote) => {
    setEditingNoteId(note.id);
    setEditingNote({
      title: note.title,
      content: note.content,
      note_type: note.note_type,
      priority: note.priority,
      is_private: note.is_private
    });
  };

  const cancelEditing = () => {
    setEditingNoteId(null);
    setEditingNote({});
  };

  const toggleExpandNote = (noteId: string) => {
    const newExpanded = new Set(expandedNotes);
    if (newExpanded.has(noteId)) {
      newExpanded.delete(noteId);
    } else {
      newExpanded.add(noteId);
    }
    setExpandedNotes(newExpanded);
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      }),
      time: date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      })
    };
  };

  const getRelativeTime = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffInMs = now.getTime() - date.getTime();
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays}d ago`;
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)}w ago`;
    if (diffInDays < 365) return `${Math.floor(diffInDays / 30)}mo ago`;
    return `${Math.floor(diffInDays / 365)}y ago`;
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high': return '🔴';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '⚪';
    }
  };

  const getNoteTypeIcon = (type: string) => {
    switch (type) {
      case 'investment': return TrendingUp;
      case 'legal': return Scale;
      case 'inspection': return Eye;
      case 'research': return Search;
      default: return FileText;
    }
  };

  const getNoteTypeLabel = (type: string) => {
    switch (type) {
      case 'investment': return 'Investment';
      case 'legal': return 'Legal';
      case 'inspection': return 'Inspection';
      case 'research': return 'Research';
      default: return 'General';
    }
  };

  // Filter notes based on search and filter
  const filteredNotes = notes.filter(note => {
    const matchesSearch = searchQuery === '' ||
      note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      note.content.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesFilter = selectedFilter === 'all' ||
      (selectedFilter === 'priority-high' && note.priority === 'high') ||
      (selectedFilter === 'private' && note.is_private) ||
      (selectedFilter === note.note_type);

    return matchesSearch && matchesFilter;
  });

  // Navy and Gold color scheme
  const navyColor = '#2c3e50';
  const goldColor = '#d4af37';
  const goldLightColor = '#f4e5c2';

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6" id="property-notes-main">
      {/* Header with Navy and Gold Theme */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6" id="property-notes-header">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold flex items-center gap-2" style={{ color: navyColor }}>
              <MessageSquare className="w-6 h-6" style={{ color: goldColor }} />
              Property Notes
            </h2>
            {propertyAddress && (
              <p className="text-sm text-gray-500 mt-1">{propertyAddress}</p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="secondary" style={{ backgroundColor: goldLightColor, color: navyColor, borderColor: goldColor }}>
              {notes.length} {notes.length === 1 ? 'Note' : 'Notes'}
            </Badge>
            {notes.length > 0 && (
              <Button
                onClick={() => setIsAddingNote(true)}
                style={{ backgroundColor: goldColor, color: navyColor }}
                className="hover:opacity-90 font-semibold"
                id="add-note-button"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Note
              </Button>
            )}
          </div>
        </div>

        {/* Search and Filter Bar */}
        {notes.length > 0 && !isAddingNote && (
          <div className="mt-4 pt-4 border-t border-gray-100 flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4" style={{ color: goldColor }} />
              <Input
                type="text"
                placeholder="Search notes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-gray-50 border-gray-200 focus:ring-2"
                style={{ focusBorderColor: goldColor }}
                id="search-notes-input"
              />
            </div>
            <select
              value={selectedFilter}
              onChange={(e) => setSelectedFilter(e.target.value)}
              className="px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2"
              style={{ focusBorderColor: goldColor }}
              id="filter-notes-select"
            >
              <option value="all">All Notes</option>
              <option value="priority-high">High Priority</option>
              <option value="private">Private Notes</option>
              <option value="investment">Investment</option>
              <option value="legal">Legal</option>
              <option value="inspection">Inspection</option>
              <option value="research">Research</option>
              <option value="general">General</option>
            </select>
          </div>
        )}
      </div>

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {/* Add New Note Form */}
      {isAddingNote && (
        <Card className="shadow-lg" style={{ borderColor: goldColor }} id="add-note-form">
          <div className="p-6 border-b border-gray-100" style={{ backgroundColor: goldLightColor }}>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold flex items-center gap-2" style={{ color: navyColor }}>
                <Plus className="w-5 h-5" style={{ color: goldColor }} />
                Create New Note
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsAddingNote(false)}
                className="text-gray-600 hover:text-red-600"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: navyColor }}>
                Title
              </label>
              <Input
                value={newNote.title}
                onChange={(e) => setNewNote({...newNote, title: e.target.value})}
                placeholder="Enter note title..."
                className="w-full"
                id="new-note-title"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: navyColor }}>
                  Type
                </label>
                <select
                  value={newNote.note_type}
                  onChange={(e) => setNewNote({...newNote, note_type: e.target.value as any})}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2"
                  style={{ focusBorderColor: goldColor }}
                  id="new-note-type"
                >
                  <option value="general">General</option>
                  <option value="investment">Investment</option>
                  <option value="legal">Legal</option>
                  <option value="inspection">Inspection</option>
                  <option value="research">Research</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: navyColor }}>
                  Priority
                </label>
                <select
                  value={newNote.priority}
                  onChange={(e) => setNewNote({...newNote, priority: e.target.value as any})}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2"
                  style={{ focusBorderColor: goldColor }}
                  id="new-note-priority"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: navyColor }}>
                  Visibility
                </label>
                <button
                  type="button"
                  onClick={() => setNewNote({...newNote, is_private: !newNote.is_private})}
                  className={`w-full px-3 py-2 border rounded-lg flex items-center justify-center gap-2 transition-colors`}
                  style={{
                    backgroundColor: newNote.is_private ? '#f9fafb' : goldLightColor,
                    borderColor: newNote.is_private ? '#d1d5db' : goldColor,
                    color: navyColor
                  }}
                  id="new-note-visibility"
                >
                  {newNote.is_private ? (
                    <>
                      <Lock className="w-4 h-4" />
                      Private
                    </>
                  ) : (
                    <>
                      <User className="w-4 h-4" />
                      Shared
                    </>
                  )}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: navyColor }}>
                Content
              </label>
              <Textarea
                value={newNote.content}
                onChange={(e) => setNewNote({...newNote, content: e.target.value})}
                placeholder="Write your note here..."
                rows={6}
                className="w-full resize-none"
                id="new-note-content"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setIsAddingNote(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={createNote}
                disabled={!newNote.title.trim() || !newNote.content.trim()}
                style={{ backgroundColor: goldColor, color: navyColor }}
                className="hover:opacity-90 font-semibold"
              >
                <Save className="w-4 h-4 mr-2" />
                Save Note
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Notes List */}
      {loading ? (
        <Card className="p-12">
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-200" style={{ borderTopColor: goldColor }}></div>
            <p className="text-gray-500">Loading notes...</p>
          </div>
        </Card>
      ) : filteredNotes.length === 0 && notes.length > 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <Filter className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2" style={{ color: navyColor }}>No matching notes</h3>
            <p className="text-gray-500">Try adjusting your search or filter criteria</p>
          </div>
        </Card>
      ) : notes.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4" style={{ backgroundColor: goldLightColor }}>
              <StickyNote className="w-8 h-8" style={{ color: goldColor }} />
            </div>
            <h3 className="text-lg font-medium mb-2" style={{ color: navyColor }}>No notes yet</h3>
            <p className="text-gray-500 mb-6">Start by adding your first note about this property</p>
            <Button
              onClick={() => setIsAddingNote(true)}
              style={{ backgroundColor: goldColor, color: navyColor }}
              className="hover:opacity-90 font-semibold"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Your First Note
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredNotes.map((note) => {
            const isExpanded = expandedNotes.has(note.id);
            const isEditing = editingNoteId === note.id;
            const TypeIcon = getNoteTypeIcon(note.note_type);
            const { date, time } = formatDateTime(note.created_at);
            const relativeTime = getRelativeTime(note.created_at);

            return (
              <Card
                key={note.id}
                className={`transition-all duration-200 hover:shadow-md ${
                  isEditing ? 'ring-2' : ''
                }`}
                style={{ ringColor: isEditing ? goldColor : undefined }}
                id={`note-card-${note.id}`}
              >
                {isEditing ? (
                  // Edit Mode
                  <div className="p-6">
                    <div className="space-y-4">
                      <Input
                        value={editingNote.title || ''}
                        onChange={(e) => setEditingNote({...editingNote, title: e.target.value})}
                        placeholder="Note title..."
                        className="font-medium"
                      />

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <select
                          value={editingNote.note_type || 'general'}
                          onChange={(e) => setEditingNote({...editingNote, note_type: e.target.value as any})}
                          className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2"
                          style={{ focusBorderColor: goldColor }}
                        >
                          <option value="general">General</option>
                          <option value="investment">Investment</option>
                          <option value="legal">Legal</option>
                          <option value="inspection">Inspection</option>
                          <option value="research">Research</option>
                        </select>

                        <select
                          value={editingNote.priority || 'medium'}
                          onChange={(e) => setEditingNote({...editingNote, priority: e.target.value as any})}
                          className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2"
                          style={{ focusBorderColor: goldColor }}
                        >
                          <option value="low">Low Priority</option>
                          <option value="medium">Medium Priority</option>
                          <option value="high">High Priority</option>
                        </select>

                        <button
                          type="button"
                          onClick={() => setEditingNote({...editingNote, is_private: !editingNote.is_private})}
                          className={`px-3 py-2 border rounded-lg flex items-center justify-center gap-2 transition-colors`}
                          style={{
                            backgroundColor: editingNote.is_private ? '#f9fafb' : goldLightColor,
                            borderColor: editingNote.is_private ? '#d1d5db' : goldColor,
                            color: navyColor
                          }}
                        >
                          {editingNote.is_private ? (
                            <>
                              <Lock className="w-4 h-4" />
                              Private
                            </>
                          ) : (
                            <>
                              <User className="w-4 h-4" />
                              Shared
                            </>
                          )}
                        </button>
                      </div>

                      <Textarea
                        value={editingNote.content || ''}
                        onChange={(e) => setEditingNote({...editingNote, content: e.target.value})}
                        rows={6}
                        className="resize-none"
                      />

                      <div className="flex items-center justify-end gap-3">
                        <Button
                          variant="outline"
                          onClick={cancelEditing}
                        >
                          Cancel
                        </Button>
                        <Button
                          onClick={() => updateNote(note.id)}
                          disabled={!editingNote.title?.trim() || !editingNote.content?.trim()}
                          style={{ backgroundColor: goldColor, color: navyColor }}
                          className="hover:opacity-90 font-semibold"
                        >
                          <Save className="w-4 h-4 mr-2" />
                          Save Changes
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  // View Mode
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-start gap-3">
                          <div className="p-2 rounded-lg" style={{ backgroundColor: goldLightColor }}>
                            <TypeIcon className="w-5 h-5" style={{ color: navyColor }} />
                          </div>
                          <div className="flex-1">
                            <h3 className="text-lg font-medium mb-1" style={{ color: navyColor }}>
                              {note.title}
                            </h3>
                            <div className="flex flex-wrap items-center gap-3 text-sm">
                              <Badge
                                variant="secondary"
                                style={{ backgroundColor: goldLightColor, color: navyColor }}
                              >
                                {getNoteTypeLabel(note.note_type)}
                              </Badge>
                              <span className="text-gray-500 flex items-center gap-1">
                                {getPriorityIcon(note.priority)} {note.priority}
                              </span>
                              {note.is_private && (
                                <Badge variant="outline" className="text-gray-600">
                                  <Lock className="w-3 h-3 mr-1" />
                                  Private
                                </Badge>
                              )}
                              <span className="text-gray-400">•</span>
                              <span className="text-gray-500" title={`${date} at ${time}`}>
                                {relativeTime}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => startEditingNote(note)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <Edit3 className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteNote(note.id)}
                          className="text-gray-400 hover:text-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    <div className="text-gray-700 whitespace-pre-wrap">
                      {isExpanded || note.content.length <= 200
                        ? note.content
                        : `${note.content.substring(0, 200)}...`}
                    </div>

                    {note.content.length > 200 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleExpandNote(note.id)}
                        className="mt-3 hover:opacity-80"
                        style={{ color: goldColor }}
                      >
                        {isExpanded ? (
                          <>
                            <ChevronUp className="w-4 h-4 mr-1" />
                            Show Less
                          </>
                        ) : (
                          <>
                            <ChevronDown className="w-4 h-4 mr-1" />
                            Show More
                          </>
                        )}
                      </Button>
                    )}

                    {note.created_by_name && (
                      <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {note.created_by_name}
                        </span>
                        {note.updated_at !== note.created_at && (
                          <span className="text-xs">
                            Edited {getRelativeTime(note.updated_at)}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}