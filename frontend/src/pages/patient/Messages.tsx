import { useState, useEffect } from "react";
import { Search, Send, Paperclip, MoreVertical } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";

import {
  getPatientConversations,
  getConversationMessages,
} from "@/api/patientService";

const PATIENT_ID = 3;

const Messages = () => {
  const [conversations, setConversations] = useState<any[]>([]);
  const [messages, setMessages] = useState<any[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<any | null>(
    null
  );

  const [searchQuery, setSearchQuery] = useState("");
  const [messageText, setMessageText] = useState("");

  const [loadingConversations, setLoadingConversations] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);

  /* ===========================
     1) Cargar conversaciones
     =========================== */
  useEffect(() => {
    const loadConversations = async () => {
      try {
        const data = await getPatientConversations(PATIENT_ID);

        const formatted = data.map((item: any) => ({
          id: item.id,
          doctor: item.doctor,
          specialty: item.specialty,
          lastMessage: item.last_message,
          time: item.time,
          unread: item.unread,
          avatar: item.avatar ?? item.doctor
            .split(" ")
            .map((n: string) => n[0])
            .join(""),
        }));

        setConversations(formatted);

        if (formatted.length > 0) {
          setSelectedConversation(formatted[0]);
        }
      } catch (err) {
        console.error("Error loading conversations:", err);
      } finally {
        setLoadingConversations(false);
      }
    };

    loadConversations();
  }, []);

  /* ======================================
     2) Cuando cambia la conversación → cargar mensajes
     ====================================== */
  useEffect(() => {
    const loadMessages = async () => {
      if (!selectedConversation) return;

      setLoadingMessages(true);

      try {
        const data = await getConversationMessages(
          PATIENT_ID,
          selectedConversation.id
        );

        const formatted = data.map((msg: any) => ({
          id: msg.id,
          sender: msg.sender,
          text: msg.text,
          time: msg.time,
        }));

        setMessages(formatted);
      } catch (err) {
        console.error("Error loading messages:", err);
      } finally {
        setLoadingMessages(false);
      }
    };

    loadMessages();
  }, [selectedConversation]);

  /* =====================
     Filtrar conversaciones
     ===================== */
  const filteredConversations = conversations.filter(
    (conv) =>
      conv.doctor.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.specialty.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-[calc(100vh-4rem)] flex bg-background">
      {/* LEFT SIDEBAR – Conversations */}
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold mb-4">Messages</h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        <ScrollArea className="flex-1">
          {loadingConversations ? (
            <p className="p-4 text-sm text-muted-foreground">
              Loading conversations...
            </p>
          ) : (
            filteredConversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => setSelectedConversation(conversation)}
                className={`p-4 border-b cursor-pointer transition-colors ${
                  selectedConversation?.id === conversation.id
                    ? "bg-primary/10"
                    : "hover:bg-muted"
                }`}
              >
                <div className="flex items-start gap-3">
                  <Avatar className="h-12 w-12 bg-primary/10">
                    <AvatarFallback className="text-primary">
                      {conversation.avatar}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="font-semibold text-sm truncate">
                        {conversation.doctor}
                      </p>
                      <span className="text-xs text-muted-foreground">
                        {conversation.time}
                      </span>
                    </div>

                    <p className="text-xs text-muted-foreground mb-1">
                      {conversation.specialty}
                    </p>

                    <p className="text-sm text-muted-foreground truncate">
                      {conversation.lastMessage}
                    </p>
                  </div>

                  {conversation.unread > 0 && (
                    <span className="bg-primary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center">
                      {conversation.unread}
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </ScrollArea>
      </div>

      {/* RIGHT SIDE – Chat */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        {selectedConversation && (
          <div className="h-16 border-b bg-card flex items-center justify-between px-6">
            <div className="flex items-center gap-3">
              <Avatar className="h-10 w-10 bg-primary/10">
                <AvatarFallback className="text-primary">
                  {selectedConversation.avatar}
                </AvatarFallback>
              </Avatar>

              <div>
                <p className="font-semibold">{selectedConversation.doctor}</p>
                <p className="text-xs text-muted-foreground">
                  {selectedConversation.specialty}
                </p>
              </div>
            </div>

            <Button variant="ghost" size="icon">
              <MoreVertical className="h-5 w-5" />
            </Button>
          </div>
        )}

        {/* Messages */}
        <ScrollArea className="flex-1 p-6">
          {loadingMessages ? (
            <p className="text-sm text-muted-foreground">Loading messages...</p>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.sender === "patient"
                      ? "justify-end"
                      : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg p-3 ${
                      message.sender === "patient"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    <p className="text-sm">{message.text}</p>
                    <p
                      className={`text-xs mt-1 ${
                        message.sender === "patient"
                          ? "text-primary-foreground/70"
                          : "text-muted-foreground"
                      }`}
                    >
                      {message.time}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Message Input */}
        <div className="border-t bg-card p-4">
          <div className="flex items-end gap-2">
            <Button variant="ghost" size="icon">
              <Paperclip className="h-5 w-5" />
            </Button>

            <Textarea
              placeholder="Type your message..."
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              className="min-h-[60px] resize-none"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  setMessageText("");
                }
              }}
            />

            <Button size="icon" className="h-[60px] w-[60px]">
              <Send className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Messages;
