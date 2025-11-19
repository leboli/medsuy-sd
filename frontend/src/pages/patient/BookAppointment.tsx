import { useEffect, useState } from "react";
import { Search, MapPin, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

import { 
  getAvailableAppointments, 
  reserveAppointment 
} from "@/api/patientService";

const PATIENT_ID = 3;

const BookAppointment = () => {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [timeOfDay, setTimeOfDay] = useState<string[]>(["afternoon"]);

  const toggleTimeOfDay = (period: string) => {
    setTimeOfDay((prev) =>
      prev.includes(period)
        ? prev.filter((p) => p !== period)
        : [...prev, period]
    );
  };

  // =============================
  // Cargar turnos disponibles
  // =============================
  const loadAppointments = async () => {
    try {
      const res = await getAvailableAppointments();

      const formatted = res.map((item: any) => {
        const dateObj = new Date(item.datetime);

        return {
          id: item.id,
          doctor: item.doctor,
          specialty: item.specialty,
          location: item.branch,
          avatar: "",
          date: dateObj.toLocaleDateString("en-US", {
            weekday: "short",
            month: "long",
            day: "numeric",
          }),
          time: dateObj.toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          }),
        };
      });

      setAppointments(formatted);
    } catch (err) {
      console.error(err);
      setError("Error loading available appointments");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppointments();
  }, []);

  // =============================
  // Reservar turno
  // =============================
  const handleReserve = async (appointmentId: number) => {
    try {
      const res = await reserveAppointment(PATIENT_ID, appointmentId);
      console.log("Reserva exitosa:", res);

      alert("Reserva realizada correctamente ✔️");

      // Volver a cargar los turnos disponibles
      loadAppointments();
    } catch (err) {
      console.error(err);
      alert("Error al reservar el turno ❌");
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-6 py-8">
        <p className="text-lg">Loading appointments...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-6 py-8">
        <p className="text-lg text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-foreground mb-2">
          Book an Appointment
        </h1>
        <p className="text-muted-foreground">
          Find and schedule your next visit with ease.
        </p>
      </div>

      <div className="grid md:grid-cols-[320px_1fr] gap-8">
        
        {/* SIDEBAR OMITIDO… */}

        {/* Results */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <p className="text-foreground">
              Showing{" "}
              <span className="font-semibold">{appointments.length} appointments</span>
            </p>
          </div>

          <div className="space-y-4">
            {appointments.map((appointment) => (
              <div
                key={appointment.id}
                className="bg-card border rounded-lg p-6 flex items-center justify-between hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-4">
                  <Avatar className="h-16 w-16">
                    <AvatarImage src={appointment.avatar} />
                    <AvatarFallback className="bg-primary/10 text-primary font-semibold">
                      {appointment.doctor
                        .split(" ")
                        .map((n) => n[0])
                        .join("")}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h3 className="font-semibold text-lg">{appointment.doctor}</h3>
                    <p className="text-sm text-muted-foreground">
                      {appointment.specialty}
                    </p>
                    <div className="flex items-center gap-1 text-sm text-muted-foreground mt-1">
                      <MapPin className="h-3 w-3" />
                      {appointment.location}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">
                      {appointment.date}
                    </p>
                    <p className="text-xl font-semibold">{appointment.time}</p>
                  </div>

                  {/* === AQUI RESERVAMOS === */}
                  <Button
                    className="bg-success hover:bg-success/90"
                    onClick={() => handleReserve(appointment.id)}
                  >
                    Book Now
                  </Button>

                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

export default BookAppointment;
