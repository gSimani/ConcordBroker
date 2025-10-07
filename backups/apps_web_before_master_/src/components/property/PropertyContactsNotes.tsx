import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  Phone,
  Mail,
  Link,
  Facebook,
  Twitter,
  Linkedin,
  Instagram,
  Globe,
  MessageSquare,
  Filter,
  Copy,
  ExternalLink,
  CheckCircle
} from 'lucide-react';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || '',
  import.meta.env.VITE_SUPABASE_ANON_KEY || ''
);

export interface PropertyNote {
  id: string;
  parcel_id: string;
  user_id?: string;
  title: string;
  content: string;
  note_type: 'general' | 'investment' | 'legal' | 'inspection' | 'research';
  priority: 'low' | 'medium' | 'high';
  is_private: boolean;
  created_at: string;
  updated_at: string;
  created_by_name?: string;
}

export interface PropertyContact {
  id: string;
  parcel_id: string;
  contact_type: 'phone' | 'email' | 'social';
  contact_value: string;
  contact_label?: string; // e.g., "Owner Mobile", "Agent Email", etc.
  contact_name?: string;
  is_primary?: boolean;
  social_platform?: string; // For social media entries
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface PropertyContactsNotesProps {
  parcelId: string;
  propertyAddress?: string;
  userId?: string;
}

export function PropertyContactsNotes({ parcelId, propertyAddress, userId }: PropertyContactsNotesProps) {
  const [notes, setNotes] = useState<PropertyNote[]>([]);
  const [contacts, setContacts] = useState<PropertyContact[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isAddingNote, setIsAddingNote] = useState(false);
  const [isAddingContact, setIsAddingContact] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [editingContactId, setEditingContactId] = useState<string | null>(null);
  const [expandedNotes, setExpandedNotes] = useState<Set<string>>(new Set());
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('notes');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Use localStorage as fallback if Supabase is not available
  const [useLocalStorage, setUseLocalStorage] = useState(false);

  // New note form state
  const [newNote, setNewNote] = useState({
    title: '',
    content: '',
    note_type: 'general' as const,
    priority: 'medium' as const,
    is_private: false
  });

  // New contact form state
  const [newContact, setNewContact] = useState({
    contact_type: 'phone' as const,
    contact_value: '',
    contact_label: '',
    contact_name: '',
    social_platform: '',
    notes: '',
    is_primary: false
  });

  // Edit states
  const [editingNote, setEditingNote] = useState<Partial<PropertyNote>>({});
  const [editingContact, setEditingContact] = useState<Partial<PropertyContact>>({});

  // Load data on mount
  useEffect(() => {
    fetchNotes();
    fetchContacts();
  }, [parcelId]);

  // Auto-dismiss success messages
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  const fetchNotes = async () => {
    if (!parcelId) return;

    setLoading(true);
    setError(null);

    // Try Supabase first
    if (!useLocalStorage) {
      try {
        const { data, error } = await supabase
          .from('property_notes')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('created_at', { ascending: false });

        if (error) {
          console.error('Supabase error:', error);
          // Fall back to localStorage
          setUseLocalStorage(true);
          loadFromLocalStorage();
        } else {
          setNotes(data || []);
        }
      } catch (error) {
        console.error('Error fetching notes:', error);
        setUseLocalStorage(true);
        loadFromLocalStorage();
      }
    } else {
      loadFromLocalStorage();
    }

    setLoading(false);
  };

  const fetchContacts = async () => {
    if (!parcelId) return;

    try {
      const { data, error } = await supabase
        .from('property_contacts')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('is_primary', { ascending: false })
        .order('created_at', { ascending: false });

      if (!error && data) {
        setContacts(data);
      } else {
        // Load from localStorage
        const stored = localStorage.getItem(`property_contacts_${parcelId}`);
        if (stored) {
          setContacts(JSON.parse(stored));
        }
      }
    } catch (error) {
      // Load from localStorage
      const stored = localStorage.getItem(`property_contacts_${parcelId}`);
      if (stored) {
        setContacts(JSON.parse(stored));
      }
    }
  };

  const loadFromLocalStorage = () => {
    const storedNotes = localStorage.getItem(`property_notes_${parcelId}`);
    if (storedNotes) {
      setNotes(JSON.parse(storedNotes));
    }
  };

  const saveToLocalStorage = (updatedNotes: PropertyNote[]) => {
    localStorage.setItem(`property_notes_${parcelId}`, JSON.stringify(updatedNotes));
  };

  const saveContactsToLocalStorage = (updatedContacts: PropertyContact[]) => {
    localStorage.setItem(`property_contacts_${parcelId}`, JSON.stringify(updatedContacts));
  };

  const createNote = async () => {
    if (!newNote.title.trim() || !newNote.content.trim()) {
      setError('Please fill in both title and content');
      return;
    }

    const noteToAdd: PropertyNote = {
      id: Date.now().toString(),
      parcel_id: parcelId,
      user_id: userId || 'anonymous',
      title: newNote.title.trim(),
      content: newNote.content.trim(),
      note_type: newNote.note_type,
      priority: newNote.priority,
      is_private: newNote.is_private,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      created_by_name: 'You'
    };

    if (!useLocalStorage) {
      try {
        const { data, error } = await supabase
          .from('property_notes')
          .insert({
            parcel_id: parcelId,
            user_id: userId || 'anonymous',
            title: newNote.title.trim(),
            content: newNote.content.trim(),
            note_type: newNote.note_type,
            priority: newNote.priority,
            is_private: newNote.is_private
          })
          .select()
          .single();

        if (error) throw error;

        setNotes([data, ...notes]);
        setSuccess('Note added successfully!');
      } catch (error) {
        console.error('Error creating note:', error);
        // Fallback to localStorage
        const updatedNotes = [noteToAdd, ...notes];
        setNotes(updatedNotes);
        saveToLocalStorage(updatedNotes);
        setSuccess('Note saved locally!');
      }
    } else {
      const updatedNotes = [noteToAdd, ...notes];
      setNotes(updatedNotes);
      saveToLocalStorage(updatedNotes);
      setSuccess('Note saved locally!');
    }

    // Reset form
    setNewNote({
      title: '',
      content: '',
      note_type: 'general',
      priority: 'medium',
      is_private: false
    });
    setIsAddingNote(false);
  };

  const createContact = async () => {
    if (!newContact.contact_value.trim()) {
      setError('Please enter contact information');
      return;
    }

    const contactToAdd: PropertyContact = {
      id: Date.now().toString(),
      parcel_id: parcelId,
      contact_type: newContact.contact_type,
      contact_value: newContact.contact_value.trim(),
      contact_label: newContact.contact_label.trim() || undefined,
      contact_name: newContact.contact_name.trim() || undefined,
      social_platform: newContact.social_platform || undefined,
      notes: newContact.notes.trim() || undefined,
      is_primary: newContact.is_primary,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    try {
      const { data, error } = await supabase
        .from('property_contacts')
        .insert(contactToAdd)
        .select()
        .single();

      if (!error && data) {
        setContacts([data, ...contacts]);
        setSuccess('Contact added successfully!');
      } else {
        // Save to localStorage as fallback
        const updatedContacts = [contactToAdd, ...contacts];
        setContacts(updatedContacts);
        saveContactsToLocalStorage(updatedContacts);
        setSuccess('Contact saved locally!');
      }
    } catch (error) {
      // Save to localStorage as fallback
      const updatedContacts = [contactToAdd, ...contacts];
      setContacts(updatedContacts);
      saveContactsToLocalStorage(updatedContacts);
      setSuccess('Contact saved locally!');
    }

    // Reset form
    setNewContact({
      contact_type: 'phone',
      contact_value: '',
      contact_label: '',
      contact_name: '',
      social_platform: '',
      notes: '',
      is_primary: false
    });
    setIsAddingContact(false);
  };

  const updateNote = async (noteId: string) => {
    if (!editingNote.title?.trim() || !editingNote.content?.trim()) {
      setError('Please fill in both title and content');
      return;
    }

    if (!useLocalStorage) {
      try {
        const { error } = await supabase
          .from('property_notes')
          .update({
            title: editingNote.title,
            content: editingNote.content,
            note_type: editingNote.note_type,
            priority: editingNote.priority,
            is_private: editingNote.is_private,
            updated_at: new Date().toISOString()
          })
          .eq('id', noteId);

        if (error) throw error;

        setSuccess('Note updated successfully!');
      } catch (error) {
        console.error('Error updating note:', error);
        setError('Failed to update note');
        return;
      }
    }

    const updatedNotes = notes.map(note =>
      note.id === noteId
        ? { ...note, ...editingNote, updated_at: new Date().toISOString() }
        : note
    );
    setNotes(updatedNotes);

    if (useLocalStorage) {
      saveToLocalStorage(updatedNotes);
      setSuccess('Note updated locally!');
    }

    setEditingNoteId(null);
    setEditingNote({});
  };

  const deleteNote = async (noteId: string) => {
    if (!confirm('Are you sure you want to delete this note?')) return;

    if (!useLocalStorage) {
      try {
        const { error } = await supabase
          .from('property_notes')
          .delete()
          .eq('id', noteId);

        if (error) throw error;

        setSuccess('Note deleted successfully!');
      } catch (error) {
        console.error('Error deleting note:', error);
        setError('Failed to delete note');
        return;
      }
    }

    const updatedNotes = notes.filter(note => note.id !== noteId);
    setNotes(updatedNotes);

    if (useLocalStorage) {
      saveToLocalStorage(updatedNotes);
      setSuccess('Note deleted locally!');
    }
  };

  const deleteContact = async (contactId: string) => {
    if (!confirm('Are you sure you want to delete this contact?')) return;

    try {
      const { error } = await supabase
        .from('property_contacts')
        .delete()
        .eq('id', contactId);

      if (!error) {
        setSuccess('Contact deleted successfully!');
      }
    } catch (error) {
      console.error('Error deleting contact:', error);
    }

    const updatedContacts = contacts.filter(c => c.id !== contactId);
    setContacts(updatedContacts);
    saveContactsToLocalStorage(updatedContacts);
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleNoteExpansion = (noteId: string) => {
    const newExpanded = new Set(expandedNotes);
    if (newExpanded.has(noteId)) {
      newExpanded.delete(noteId);
    } else {
      newExpanded.add(noteId);
    }
    setExpandedNotes(newExpanded);
  };

  const filteredNotes = notes.filter(note => {
    const matchesFilter = selectedFilter === 'all' || note.note_type === selectedFilter;
    const matchesSearch = note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          note.content.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getNoteIcon = (type: string) => {
    switch (type) {
      case 'investment': return <TrendingUp className="w-3 h-3" />;
      case 'legal': return <Scale className="w-3 h-3" />;
      case 'inspection': return <Eye className="w-3 h-3" />;
      case 'research': return <Search className="w-3 h-3" />;
      default: return <FileText className="w-3 h-3" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSocialIcon = (platform: string) => {
    switch (platform?.toLowerCase()) {
      case 'facebook': return <Facebook className="w-4 h-4" />;
      case 'twitter': return <Twitter className="w-4 h-4" />;
      case 'linkedin': return <Linkedin className="w-4 h-4" />;
      case 'instagram': return <Instagram className="w-4 h-4" />;
      default: return <Globe className="w-4 h-4" />;
    }
  };

  return (
    <Card className="elegant-card">
      <div className="p-6">
        <h3 className="text-lg font-semibold text-navy mb-4 flex items-center">
          <MessageSquare className="w-5 h-5 mr-2 text-gold" />
          Property Information Hub
        </h3>

        {/* Success/Error Messages */}
        {success && (
          <Alert className="mb-4 bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">{success}</AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert className="mb-4 bg-red-50 border-red-200">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2 mb-4">
            <TabsTrigger value="notes">
              <StickyNote className="w-4 h-4 mr-2" />
              Notes ({filteredNotes.length})
            </TabsTrigger>
            <TabsTrigger value="contacts">
              <Phone className="w-4 h-4 mr-2" />
              Contacts ({contacts.length})
            </TabsTrigger>
          </TabsList>

          {/* Notes Tab */}
          <TabsContent value="notes">
            {/* Filter and Search */}
            <div className="flex flex-wrap gap-2 mb-4">
              <div className="flex-1 min-w-[200px]">
                <Input
                  placeholder="Search notes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full"
                />
              </div>
              <select
                value={selectedFilter}
                onChange={(e) => setSelectedFilter(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm"
              >
                <option value="all">All Types</option>
                <option value="general">General</option>
                <option value="investment">Investment</option>
                <option value="legal">Legal</option>
                <option value="inspection">Inspection</option>
                <option value="research">Research</option>
              </select>
            </div>

            {/* Add Note Button */}
            {!isAddingNote && (
              <Button
                onClick={() => setIsAddingNote(true)}
                className="w-full mb-4"
                style={{ backgroundColor: '#d4af37', color: '#2c3e50' }}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add New Note
              </Button>
            )}

            {/* Add Note Form */}
            {isAddingNote && (
              <div className="mb-4 p-4 border rounded-lg bg-gray-50">
                <div className="space-y-3">
                  <Input
                    placeholder="Note title..."
                    value={newNote.title}
                    onChange={(e) => setNewNote({ ...newNote, title: e.target.value })}
                  />
                  <Textarea
                    placeholder="Note content..."
                    value={newNote.content}
                    onChange={(e) => setNewNote({ ...newNote, content: e.target.value })}
                    rows={4}
                  />
                  <div className="flex gap-2">
                    <select
                      value={newNote.note_type}
                      onChange={(e) => setNewNote({ ...newNote, note_type: e.target.value as any })}
                      className="px-3 py-2 border rounded-md text-sm"
                    >
                      <option value="general">General</option>
                      <option value="investment">Investment</option>
                      <option value="legal">Legal</option>
                      <option value="inspection">Inspection</option>
                      <option value="research">Research</option>
                    </select>
                    <select
                      value={newNote.priority}
                      onChange={(e) => setNewNote({ ...newNote, priority: e.target.value as any })}
                      className="px-3 py-2 border rounded-md text-sm"
                    >
                      <option value="low">Low Priority</option>
                      <option value="medium">Medium Priority</option>
                      <option value="high">High Priority</option>
                    </select>
                  </div>
                  <div className="flex justify-between">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={newNote.is_private}
                        onChange={(e) => setNewNote({ ...newNote, is_private: e.target.checked })}
                        className="mr-2"
                      />
                      <span className="text-sm">Private note</span>
                    </label>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => {
                          setIsAddingNote(false);
                          setNewNote({
                            title: '',
                            content: '',
                            note_type: 'general',
                            priority: 'medium',
                            is_private: false
                          });
                        }}
                        variant="outline"
                        size="sm"
                      >
                        <X className="w-4 h-4 mr-1" />
                        Cancel
                      </Button>
                      <Button
                        onClick={createNote}
                        size="sm"
                        style={{ backgroundColor: '#d4af37', color: '#2c3e50' }}
                      >
                        <Save className="w-4 h-4 mr-1" />
                        Save Note
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Notes List */}
            <div className="space-y-3">
              {loading ? (
                <div className="text-center py-8 text-gray-500">Loading notes...</div>
              ) : filteredNotes.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <StickyNote className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No notes yet for this property</p>
                  <p className="text-sm mt-1">Add your first note to get started</p>
                </div>
              ) : (
                filteredNotes.map((note) => (
                  <div
                    key={note.id}
                    className={`border rounded-lg p-4 ${getPriorityColor(note.priority)}`}
                  >
                    {editingNoteId === note.id ? (
                      // Edit Mode
                      <div className="space-y-3">
                        <Input
                          value={editingNote.title || ''}
                          onChange={(e) => setEditingNote({ ...editingNote, title: e.target.value })}
                        />
                        <Textarea
                          value={editingNote.content || ''}
                          onChange={(e) => setEditingNote({ ...editingNote, content: e.target.value })}
                          rows={4}
                        />
                        <div className="flex gap-2">
                          <select
                            value={editingNote.note_type}
                            onChange={(e) => setEditingNote({ ...editingNote, note_type: e.target.value as any })}
                            className="px-3 py-2 border rounded-md text-sm"
                          >
                            <option value="general">General</option>
                            <option value="investment">Investment</option>
                            <option value="legal">Legal</option>
                            <option value="inspection">Inspection</option>
                            <option value="research">Research</option>
                          </select>
                          <select
                            value={editingNote.priority}
                            onChange={(e) => setEditingNote({ ...editingNote, priority: e.target.value as any })}
                            className="px-3 py-2 border rounded-md text-sm"
                          >
                            <option value="low">Low Priority</option>
                            <option value="medium">Medium Priority</option>
                            <option value="high">High Priority</option>
                          </select>
                        </div>
                        <div className="flex justify-end gap-2">
                          <Button
                            onClick={() => {
                              setEditingNoteId(null);
                              setEditingNote({});
                            }}
                            variant="outline"
                            size="sm"
                          >
                            Cancel
                          </Button>
                          <Button
                            onClick={() => updateNote(note.id)}
                            size="sm"
                            style={{ backgroundColor: '#d4af37', color: '#2c3e50' }}
                          >
                            <Save className="w-4 h-4 mr-1" />
                            Save Changes
                          </Button>
                        </div>
                      </div>
                    ) : (
                      // View Mode
                      <>
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-start gap-2">
                            {getNoteIcon(note.note_type)}
                            <div>
                              <h4 className="font-semibold text-navy">{note.title}</h4>
                              <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
                                <Calendar className="w-3 h-3" />
                                {new Date(note.created_at).toLocaleDateString()}
                                <Clock className="w-3 h-3 ml-2" />
                                {new Date(note.created_at).toLocaleTimeString()}
                                {note.is_private && (
                                  <Badge variant="outline" className="ml-2">
                                    <Lock className="w-3 h-3 mr-1" />
                                    Private
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            <Button
                              onClick={() => toggleNoteExpansion(note.id)}
                              variant="ghost"
                              size="sm"
                            >
                              {expandedNotes.has(note.id) ? (
                                <ChevronUp className="w-4 h-4" />
                              ) : (
                                <ChevronDown className="w-4 h-4" />
                              )}
                            </Button>
                            <Button
                              onClick={() => {
                                setEditingNoteId(note.id);
                                setEditingNote(note);
                              }}
                              variant="ghost"
                              size="sm"
                            >
                              <Edit3 className="w-4 h-4" />
                            </Button>
                            <Button
                              onClick={() => deleteNote(note.id)}
                              variant="ghost"
                              size="sm"
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                        <div className={`text-sm text-gray-700 ${!expandedNotes.has(note.id) ? 'line-clamp-2' : ''}`}>
                          {note.content}
                        </div>
                      </>
                    )}
                  </div>
                ))
              )}
            </div>
          </TabsContent>

          {/* Contacts Tab */}
          <TabsContent value="contacts">
            {/* Add Contact Button */}
            {!isAddingContact && (
              <Button
                onClick={() => setIsAddingContact(true)}
                className="w-full mb-4"
                style={{ backgroundColor: '#d4af37', color: '#2c3e50' }}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Contact Information
              </Button>
            )}

            {/* Add Contact Form */}
            {isAddingContact && (
              <div className="mb-4 p-4 border rounded-lg bg-gray-50">
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      value={newContact.contact_type}
                      onChange={(e) => setNewContact({ ...newContact, contact_type: e.target.value as any })}
                      className="px-3 py-2 border rounded-md text-sm"
                    >
                      <option value="phone">Phone</option>
                      <option value="email">Email</option>
                      <option value="social">Social Media</option>
                    </select>
                    {newContact.contact_type === 'social' && (
                      <Input
                        placeholder="Platform (Facebook, Twitter, etc.)"
                        value={newContact.social_platform}
                        onChange={(e) => setNewContact({ ...newContact, social_platform: e.target.value })}
                      />
                    )}
                  </div>
                  <Input
                    placeholder={
                      newContact.contact_type === 'phone' ? 'Phone number...' :
                      newContact.contact_type === 'email' ? 'Email address...' :
                      'Profile URL or username...'
                    }
                    value={newContact.contact_value}
                    onChange={(e) => setNewContact({ ...newContact, contact_value: e.target.value })}
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <Input
                      placeholder="Contact name (optional)"
                      value={newContact.contact_name}
                      onChange={(e) => setNewContact({ ...newContact, contact_name: e.target.value })}
                    />
                    <Input
                      placeholder="Label (e.g., Owner, Agent)"
                      value={newContact.contact_label}
                      onChange={(e) => setNewContact({ ...newContact, contact_label: e.target.value })}
                    />
                  </div>
                  <Textarea
                    placeholder="Notes about this contact (optional)"
                    value={newContact.notes}
                    onChange={(e) => setNewContact({ ...newContact, notes: e.target.value })}
                    rows={2}
                  />
                  <div className="flex justify-between">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={newContact.is_primary}
                        onChange={(e) => setNewContact({ ...newContact, is_primary: e.target.checked })}
                        className="mr-2"
                      />
                      <span className="text-sm">Primary contact</span>
                    </label>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => {
                          setIsAddingContact(false);
                          setNewContact({
                            contact_type: 'phone',
                            contact_value: '',
                            contact_label: '',
                            contact_name: '',
                            social_platform: '',
                            notes: '',
                            is_primary: false
                          });
                        }}
                        variant="outline"
                        size="sm"
                      >
                        <X className="w-4 h-4 mr-1" />
                        Cancel
                      </Button>
                      <Button
                        onClick={createContact}
                        size="sm"
                        style={{ backgroundColor: '#d4af37', color: '#2c3e50' }}
                      >
                        <Save className="w-4 h-4 mr-1" />
                        Save Contact
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Contacts List */}
            <div className="space-y-3">
              {contacts.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Phone className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No contacts saved for this property</p>
                  <p className="text-sm mt-1">Add phone numbers, emails, and social media</p>
                </div>
              ) : (
                <>
                  {/* Phone Numbers */}
                  {contacts.filter(c => c.contact_type === 'phone').length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                        <Phone className="w-4 h-4 mr-2" />
                        Phone Numbers
                      </h4>
                      <div className="space-y-2">
                        {contacts.filter(c => c.contact_type === 'phone').map((contact) => (
                          <div key={contact.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-navy">{contact.contact_value}</span>
                                {contact.is_primary && (
                                  <Badge className="bg-gold text-white">Primary</Badge>
                                )}
                                {contact.contact_label && (
                                  <Badge variant="outline">{contact.contact_label}</Badge>
                                )}
                              </div>
                              {contact.contact_name && (
                                <p className="text-sm text-gray-600 mt-1">{contact.contact_name}</p>
                              )}
                              {contact.notes && (
                                <p className="text-xs text-gray-500 mt-1">{contact.notes}</p>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <Button
                                onClick={() => copyToClipboard(contact.contact_value, contact.id)}
                                variant="ghost"
                                size="sm"
                              >
                                {copiedId === contact.id ? (
                                  <CheckCircle className="w-4 h-4 text-green-600" />
                                ) : (
                                  <Copy className="w-4 h-4" />
                                )}
                              </Button>
                              <a href={`tel:${contact.contact_value}`}>
                                <Button variant="ghost" size="sm">
                                  <Phone className="w-4 h-4" />
                                </Button>
                              </a>
                              <Button
                                onClick={() => deleteContact(contact.id)}
                                variant="ghost"
                                size="sm"
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Emails */}
                  {contacts.filter(c => c.contact_type === 'email').length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                        <Mail className="w-4 h-4 mr-2" />
                        Email Addresses
                      </h4>
                      <div className="space-y-2">
                        {contacts.filter(c => c.contact_type === 'email').map((contact) => (
                          <div key={contact.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-navy">{contact.contact_value}</span>
                                {contact.is_primary && (
                                  <Badge className="bg-gold text-white">Primary</Badge>
                                )}
                                {contact.contact_label && (
                                  <Badge variant="outline">{contact.contact_label}</Badge>
                                )}
                              </div>
                              {contact.contact_name && (
                                <p className="text-sm text-gray-600 mt-1">{contact.contact_name}</p>
                              )}
                              {contact.notes && (
                                <p className="text-xs text-gray-500 mt-1">{contact.notes}</p>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <Button
                                onClick={() => copyToClipboard(contact.contact_value, contact.id)}
                                variant="ghost"
                                size="sm"
                              >
                                {copiedId === contact.id ? (
                                  <CheckCircle className="w-4 h-4 text-green-600" />
                                ) : (
                                  <Copy className="w-4 h-4" />
                                )}
                              </Button>
                              <a href={`mailto:${contact.contact_value}`}>
                                <Button variant="ghost" size="sm">
                                  <Mail className="w-4 h-4" />
                                </Button>
                              </a>
                              <Button
                                onClick={() => deleteContact(contact.id)}
                                variant="ghost"
                                size="sm"
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Social Media */}
                  {contacts.filter(c => c.contact_type === 'social').length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                        <Globe className="w-4 h-4 mr-2" />
                        Social Media
                      </h4>
                      <div className="space-y-2">
                        {contacts.filter(c => c.contact_type === 'social').map((contact) => (
                          <div key={contact.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                {getSocialIcon(contact.social_platform)}
                                <span className="font-medium text-navy">{contact.contact_value}</span>
                                {contact.social_platform && (
                                  <Badge variant="outline">{contact.social_platform}</Badge>
                                )}
                              </div>
                              {contact.contact_name && (
                                <p className="text-sm text-gray-600 mt-1">{contact.contact_name}</p>
                              )}
                              {contact.notes && (
                                <p className="text-xs text-gray-500 mt-1">{contact.notes}</p>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <Button
                                onClick={() => copyToClipboard(contact.contact_value, contact.id)}
                                variant="ghost"
                                size="sm"
                              >
                                {copiedId === contact.id ? (
                                  <CheckCircle className="w-4 h-4 text-green-600" />
                                ) : (
                                  <Copy className="w-4 h-4" />
                                )}
                              </Button>
                              <a href={contact.contact_value.startsWith('http') ? contact.contact_value : `https://${contact.contact_value}`} target="_blank" rel="noopener noreferrer">
                                <Button variant="ghost" size="sm">
                                  <ExternalLink className="w-4 h-4" />
                                </Button>
                              </a>
                              <Button
                                onClick={() => deleteContact(contact.id)}
                                variant="ghost"
                                size="sm"
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </TabsContent>
        </Tabs>

        {/* Storage Indicator */}
        {useLocalStorage && (
          <div className="mt-4 p-2 bg-yellow-50 rounded-lg border border-yellow-200">
            <p className="text-xs text-yellow-700 flex items-center">
              <AlertCircle className="w-3 h-3 mr-1" />
              Using local storage. Sign in to sync across devices.
            </p>
          </div>
        )}
      </div>
    </Card>
  );
}