"""CSC343 Assignment 2

=== CSC343 Winter 2023 ===
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC343 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Danny Heap, Marina Tawfik, and Jacqueline Smith

All of the files in this directory and all subdirectories are:
Copyright (c) 2023 Danny Heap and Jacqueline Smith

=== Module Description ===

This file contains the WasteWrangler class and some simple testing functions.
"""

import datetime as dt
import psycopg2 as pg
import psycopg2.extensions as pg_ext
import psycopg2.extras as pg_extras
from typing import Optional, TextIO


class WasteWrangler:
    """A class that can work with data conforming to the schema in
    waste_wrangler_schema.ddl.

    === Instance Attributes ===
    connection: connection to a PostgreSQL database of a waste management
    service.

    Representation invariants:
    - The database to which connection is established conforms to the schema
      in waste_wrangler_schema.ddl.
    """
    connection: Optional[pg_ext.connection]

    def __init__(self) -> None:
        """Initialize this WasteWrangler instance, with no database connection
        yet.
        """
        self.connection = None

    def connect(self, dbname: str, username: str, password: str) -> bool:
        """Establish a connection to the database <dbname> using the
        username <username> and password <password>, and assign it to the
        instance attribute <connection>. In addition, set the search path
        to waste_wrangler.

        Return True if the connection was made successfully, False otherwise.
        I.e., do NOT throw an error if making the connection fails.

        ww = WasteWrangler()
        ww.connect("csc343h-marinat", "marinat", "")
        True
        # In this example, the connection cannot be made.
        ww.connect("invalid", "nonsense", "incorrect")
        False
        """
        try:
            self.connection = pg.connect(
                dbname=dbname, user=username, password=password,
                options="-c search_path=waste_wrangler"
            )
            return True
        except pg.Error:
            return False

    def disconnect(self) -> bool:
        """Close this WasteWrangler's connection to the database.

        Return True if closing the connection was successful, False otherwise.
        I.e., do NOT throw an error if closing the connection failed.

        ww = WasteWrangler()
        ww.connect("csc343h-marinat", "marinat", "")
        True
        ww.disconnect()
        True
        """
        try:
            if self.connection and not self.connection.closed:
                self.connection.close()
            return True
        except pg.Error:
            return False

    def schedule_trip(self, rid: int, time: dt.datetime) -> bool:
        """Schedule a truck and two employees to the route identified
        with <rid> at the given time stamp <time> to pick up an
        unknown volume of waste, and deliver it to the appropriate facility.

        The employees and truck selected for this trip must be available:
            * They can NOT be scheduled for a different trip from 30 minutes
              of the expected start until 30 minutes after the end time of this
              trip.
            * The truck can NOT be scheduled for maintenance on the same day.

        The end time of a trip can be computed by assuming that all trucks
        travel at an average of 5 kph.

        From the available trucks, pick a truck that can carry the same
        waste type as <rid> and give priority based on larger capacity and
        use the ascending order of ids to break ties.

        From the available employees, give preference based on hireDate
        (employees who have the most experience get priority), and order by
        ascending order of ids in case of ties, such that at least one
        employee can drive the truck type of the selected truck.

        Pick a facility that has the same waste type a <rid> and select the one
        with the lowest fID.

        Return True iff a trip has been scheduled successfully for the given
            route.
        This method should NOT throw an error i.e. if scheduling fails, the
        method should simply return False.

        No changes should be made to the database if scheduling the trip fails.

        Scheduling fails i.e., the method returns False, if any of the following
        is true:
            * If rid is an invalid route ID.
            * If no appropriate truck, drivers or facility can be found.
                        * If a trip has already been scheduled for <rid> on the same day
              as <time> (that encompasses the exact same time as <time>).
            * If the trip can't be scheduled within working hours i.e., between
              8:00-16:00.

        While a realistic use case will provide a <time> in the near future, our
        tests could use any valid value for <time>.
        """
        # Maintenance(tID, eID, date)
        # Employee(eID, name, hireDate) Driver(eID, truckType)
        # Truck(tID, truckType, capacity) TruckType(truckType, wasteType) Facility(fID, address, wasteType) Route(rID, wasteType, length)
        # try:
        # TODO: implement this method
        cursor1 = self.connection.cursor()
        # check for valid rid
        cursor1.execute("select * from Route where rid = {};".format(rid))
        if cursor1.rowcount == 0:
            cursor1.close()
            print("invalid rid")
            return False
        # check if there is a trip already scheduled
        cursor1.execute("select rid from Trip where rid = {} and ttime::date = '{}';".format(rid, time.date()))
        if cursor1.rowcount != 0:
            cursor1.close()
            print("Trip scheduled")
            return False
        # check if there is a facility with corresponding wastetype
        cursor1.execute("SELECT fid \
                             FROM facility, truck, Route, TruckType \
                             WHERE truck.trucktype = TruckType.trucktype and TruckType.wastetype = Route.wastetype and TruckType.wastetype = facility.wastetype and Route.rid = {} \
                             ORDER BY fid ASC;".format(rid))
        if cursor1.rowcount == 0:
            cursor1.close()
            print("No facility")
            return False
        available_facility = cursor1.fetchone()[0]
        # At this point, our rid should be valid, so our fetchall won't return an empty list
        # fetchall returns a list of tuples
        # find the waste type of corresponding to rid
        cursor1.execute("SELECT wastetype FROM Route WHERE rid = {};".format(rid))
        wastetype = cursor1.fetchone()[0]
        cursor1.execute("SELECT length FROM Route WHERE rid = {};".format(rid))
        length = cursor1.fetchone()[0]
        endtime = time + dt.timedelta(hours=length / 5)
        # check if the time falls in 8:00:00 and 16:00:00 on the same date
        eight_am = dt.datetime(time.year, time.month, time.day, 8, 0, 0)
        four_pm = dt.datetime(time.year, time.month, time.day, 16, 0, 0)
        cursor1.execute("SELECT * \
                             FROM Route \
                             WHERE rid = {} and '{}' BETWEEN '{}' and '{}' and '{}' BETWEEN '{}' and '{}';".format(rid,
                                                                                                                   time,
                                                                                                                   eight_am,
                                                                                                                   four_pm,
                                                                                                                   endtime,
                                                                                                                   eight_am,
                                                                                                                   four_pm))

        legal_time = cursor1.fetchall()
        if len(legal_time) == 0 or time.day != endtime.day:
            cursor1.close()
            print("Not in working hours")
            return False
        # find the trucks that is not in maintenance, no trip in 30 minutes prior to this trip or overlapping in the time interval
        # no trip after its end time (endtime)
        cursor1.execute(" \
                         SELECT t1.tid tid, t1.trucktype trucktype, t1.capacity capacity \
                         FROM Truck t1 NATURAL JOIN TruckType ty1 NATURAL JOIN maintenance \
                         WHERE ty1.wastetype = '{}' and maintenance.mdate != '{}' and NOT EXISTS( \
                            SELECT * \
                            FROM Route r1 NATURAL JOIN Trip tr1 \
                            WHERE  t1.tid = tr1.tid and (tr1.ttime BETWEEN '{}' and '{}' or (tr1.ttime + (interval '1 hour' * r1.length/5)) BETWEEN '{}' and '{}' \
                                   or ('{}', '{}')OVERLAPS (tr1.ttime, (tr1.ttime + (interval '1 hour' * r1.length/5)))))\
                         ORDER BY t1.capacity DESC, t1.tid ASC;".format(wastetype,
                                                                        dt.date(time.year, time.month,
                                                                                time.day),
                                                                        time - dt.timedelta(minutes=30),
                                                                        endtime + dt.timedelta(minutes=30),
                                                                        time - dt.timedelta(minutes=30),
                                                                        endtime + dt.timedelta(minutes=30),
                                                                        time - dt.timedelta(minutes=30),
                                                                        time + dt.timedelta(minutes=30)))
        if cursor1.rowcount == 0:
            cursor1.close()
            print("No Truck Available")
            return False
        truck_find = cursor1.fetchall()  # list of tuples
        # find all the available employees
        cursor1.execute("CREATE VIEW All_drivers_available AS \
                             SELECT d1.eid eid \
                             FROM Driver d1 JOIN Employee e1 ON d1.eid = e1.eid\
                             WHERE NOT EXISTS ( \
                                 SELECT * \
                                 FROM Route r1 NATURAL JOIN Trip tr1 \
                                 WHERE (tr1.eid1 = d1.eid or tr1.eid2 = d1.eid) and (tr1.ttime BETWEEN '{}' and '{}' or (tr1.ttime + (interval '1 hour' * r1.length/5)) BETWEEN '{}' and '{}' \
                                           or ('{}', '{}')OVERLAPS (tr1.ttime, (tr1.ttime + (interval '1 hour' * r1.length/5))))\
                             ) \
                             ORDER BY e1.hiredate ASC;"
                        .format(time - dt.timedelta(minutes=30),
                                endtime + dt.timedelta(minutes=30),
                                time - dt.timedelta(minutes=30),
                                endtime + dt.timedelta(minutes=30),
                                time - dt.timedelta(minutes=30),
                                endtime + dt.timedelta(minutes=30)))
        # if len(cursor1.fetchall()) == 0:
        #     cursor1.close()
        #     print("No available employees")
        #     return False
        cursor1.execute("SELECT a1.eid eid1, a2.eid eid2\
                         FROM All_drivers_available a1, All_drivers_available a2 \
                         WHERE a1.eid != a2.eid and EXISTS ( \
                            SELECT * \
                            FROM All_drivers_available a3 JOIN Driver d2 ON d2.eid = a3.eid\
                            WHERE (d2.eid = a1.eid or d2.eid = a2.eid) and d2.trucktype = '{}'\
                         );".format(truck_find[0][1]))
        # pair_drivers = cursor1.fetchone()
        if cursor1.rowcount == 0:
            print("No drivers")
            return False
        pair_drivers = cursor1.fetchone()
        cursor1.execute(
            "INSERT INTO Trip VALUES ({}, {}, '{}', NULL, {}, {}, {});".format(rid, truck_find[0][0], time,
                                                                               pair_drivers[0], pair_drivers[1],
                                                                               available_facility))
        cursor1.execute("DROP VIEW All_drivers_available CASCADE;")
        self.connection.commit()
        return True
        # try:
        #
        # except pg.Error as ex:
        #     # You may find it helpful to uncomment this line while debugging,
        #     # as it will show you all the details of the error that occurred:
        #     # raise ex
        #     print("PG Error")
        #     return False

    def schedule_trips(self, tid: int, date: dt.date) -> int:
        """Schedule the truck identified with <tid> for trips on <date> using
        the following approach:

            1. Find routes not already scheduled for <date>, for which <tid>
               is able to carry the waste type. Schedule these by ascending
               order of rIDs.

            2. Starting from 8 a.m., find the earliest available pair
               of drivers who are available all day. Give preference
               based on hireDate (employees who have the most
               experience get priority), and break ties by choosing
               the lower eID, such that at least one employee can
               drive the truck type of <tid>.

               The facility for the trip is the one with the lowest fID that can
               handle the waste type of the route.

               The volume for the scheduled trip should be null.

            3. Continue scheduling, making sure to leave 30 minutes between
               the end of one trip and the start of the next, using the
               assumption that <tid> will travel an average of 5 kph.
               Make sure that the last trip will not end after 4 p.m.

        Return the number of trips that were scheduled successfully.

        Your method should NOT raise an error.

        While a realistic use case will provide a <date> in the near future, our
        tests could use any valid value for <date>.
        """
        # TODO: implement this method
        pass

    def update_technicians(self, qualifications_file: TextIO) -> int:
        """Given the open file <qualifications_file> that follows the format
        described on the handout, update the database to reflect that the
        recorded technicians can now work on the corresponding given truck type.

        For the purposes of this method, you may assume that no two employees
        in our database have the same name i.e., an employee can be uniquely
        identified using their name.

        Your method should NOT throw an error.
        Instead, only correct entries should be reflected in the database.
        Return the number of successful changes, which is the same as the number
        of valid entries.
        Invalid entries include:
            * Incorrect employee name.
            * Incorrect truck type.
            * The technician is already recorded to work on the corresponding
              truck type.
            * The employee is a driver.

        Hint: We have provided a helper _read_qualifications_file that you
            might find helpful for completing this method.
        """
        try:
            # TODO: implement this method
            pass
        except pg.Error as ex:
            # You may find it helpful to uncomment this line while debugging,
            # as it will show you all the details of the error that occurred:
            # raise ex
            return 0

    def workmate_sphere(self, eid: int) -> list[int]:
        """Return the workmate sphere of the driver identified by <eid>, as a
        list of eIDs.
        The workmate sphere of <eid> is:
            * Any employee who has been on a trip with <eid>.
            * Recursively, any employee who has been on a trip with an employee
              in <eid>'s workmate sphere is also in <eid>'s workmate sphere.
        The returned list should NOT include <eid> and should NOT include
        duplicates.
        The order of the returned ids does NOT matter.
        Your method should NOT return an error. If an error occurs, your method
        should simply return an empty list.
        """
        try:
            # TODO: implement this method
            sphere_queue = []  # the frontier queue used to keep expanding
            workmate = []  # the actual list to return
            workmate_set = set()  # the set used to prevent duplicate

            cursor = self.connection.cursor()
            cursor.execute("SELECT eid1, eid2 FROM Trip WHERE Trip.eid1 = {} or Trip.eid2 = {};".format(eid, eid))
            if cursor.rowcount == 0:
                return []
            initial_tuple = cursor.fetchall()

            for x in initial_tuple:
                if x[0] == eid:
                    if x[1] not in workmate_set:
                        workmate_set.add(x[1])
                        sphere_queue.append(x[1])
                        workmate.append(x[1])
                else:
                    if x[0] not in workmate_set:
                        workmate_set.add(x[0])
                        sphere_queue.append(x[0])
                        workmate.append(x[0])
            while len(sphere_queue):
                next_workmate = sphere_queue.pop()
                cursor.execute("SELECT eid1, eid2 FROM Trip WHERE Trip.eid1 = {} or Trip.eid2 = {};".format(next_workmate, next_workmate))
                if cursor.rowcount == 0:
                    continue
                next_tuple = cursor.fetchall()
                for y in next_tuple:
                    if y[0] == eid:
                        if y[1] not in workmate_set:
                            workmate_set.add(y[1])
                            sphere_queue.append(y[1])
                            workmate.append(y[1])
                    else:
                        if y[0] not in workmate_set:
                            workmate_set.add(y[0])
                            sphere_queue.append(y[0])
                            workmate.append(y[0])

            return workmate
        except pg.Error as ex:
            # You may find it helpful to uncomment this line while debugging,
            # as it will show you all the details of the error that occurred:
            # raise ex
            return []

    def schedule_maintenance(self, date: dt.date) -> int:
        """For each truck whose most recent maintenance before <date> happened
        over 90 days before <date>, and for which there is no scheduled
        maintenance up to 10 days following date, schedule maintenance with
        a technician qualified to work on that truck in ascending order of tIDs.

        For example, if <date> is 2023-05-02, then you should consider trucks
        that had maintenance before 2023-02-01, and for which there is no
        scheduled maintenance from 2023-05-02 to 2023-05-12 inclusive.

        Choose the first day after <date> when there is a qualified technician
        available (not scheduled to maintain another truck that day) and the
        truck is not scheduled for a trip or maintenance on that day.

        If there is more than one technician available on a given day, choose
        the one with the lowest eID.

        Return the number of trucks that were successfully scheduled for
        maintenance.

        Your method should NOT throw an error.

        While a realistic use case will provide a <date> in the near future, our
        tests could use any valid value for <date>.
        """
        try:
            # TODO: implement this method
            pass
        except pg.Error as ex:
            # You may find it helpful to uncomment this line while debugging,
            # as it will show you all the details of the error that occurred:
            # raise ex
            return 0

    def reroute_waste(self, fid: int, date: dt.date) -> int:
        """Reroute the trips to <fid> on day <date> to another facility that
        takes the same type of waste. If there are many such facilities, pick
        the one with the smallest fID (that is not <fid>).

        Return the number of re-routed trips.

        Don't worry about too many trips arriving at the same time to the same
        facility. Each facility has ample receiving facility.

        Your method should NOT return an error. If an error occurs, your method
        should simply return 0 i.e., no trips have been re-routed.

        While a realistic use case will provide a <date> in the near future, our
        tests could use any valid value for <date>.

        Assume this happens before any of the trips have reached <fid>.
        """
        try:
            # TODO: implement this method
            pass
        except pg.Error as ex:
            # You may find it helpful to uncomment this line while debugging,
            # as it will show you all the details of the error that occurred:
            # raise ex
            return 0

    # =========================== Helper methods ============================= #

    @staticmethod
    def _read_qualifications_file(file: TextIO) -> list[list[str, str, str]]:
        """Helper for update_technicians. Accept an open file <file> that
        follows the format described on the A2 handout and return a list
        representing the information in the file, where each item in the list
        includes the following 3 elements in this order:
            * The first name of the technician.
            * The last name of the technician.
            * The truck type that the technician is currently qualified to work
              on.

        Pre-condition:
            <file> follows the format given on the A2 handout.
        """
        result = []
        employee_info = []
        for idx, line in enumerate(file):
            if idx % 2 == 0:
                info = line.strip().split(' ')[-2:]
                fname, lname = info
                employee_info.extend([fname, lname])
            else:
                employee_info.append(line.strip())
                result.append(employee_info)
                employee_info = []

        return result


def setup(dbname: str, username: str, password: str, file_path: str) -> None:
    """Set up the testing environment for the database <dbname> using the
    username <username> and password <password> by importing the schema file
    and the file containing the data at <file_path>.
    """
    connection, cursor, schema_file, data_file = None, None, None, None
    try:
        # Change this to connect to your own database
        connection = pg.connect(
            dbname=dbname, user=username, password=password,
            options="-c search_path=waste_wrangler"
        )
        cursor = connection.cursor()

        schema_file = open("./waste_wrangler_schema.sql", "r")
        cursor.execute(schema_file.read())

        data_file = open(file_path, "r")
        cursor.execute(data_file.read())

        connection.commit()
    except Exception as ex:
        connection.rollback()
        raise Exception(f"Couldn't set up environment for tests: \n{ex}")
    finally:
        if cursor and not cursor.closed:
            cursor.close()
        if connection and not connection.closed:
            connection.close()
        if schema_file:
            schema_file.close()
        if data_file:
            data_file.close()


def test_preliminary() -> None:
    """Test preliminary aspects of the A2 methods."""
    ww = WasteWrangler()
    qf = None
    try:
        # TODO: Change the values of the following variables to connect to your
        #  own database:
        dbname = 'csc343h-jishuli1'
        user = 'jishuli1'
        password = 'jsl20011024'

        connected = ww.connect(dbname, user, password)

        # The following is an assert statement. It checks that the value for
        # connected is True. The message after the comma will be printed if
        # that is not the case (connected is False).
        # Use the same notation to thoroughly test the methods we have provided
        assert connected, f"[Connected] Expected True | Got {connected}."

        # TODO: Test one or more methods here, or better yet, make more testing
        #   functions, with each testing a different aspect of the code.

        # The following function will set up the testing environment by loading
        # the sample data we have provided into your database. You can create
        # more sample data files and use the same function to load them into
        # your database.
        # Note: make sure that the schema and data files are in the same
        # directory (folder) as your a2.py file.
        setup(dbname, user, password, './waste_wrangler_data.sql')

        # --------------------- Testing schedule_trip  ------------------------#

        # You will need to check that data in the Trip relation has been
        # changed accordingly. The following row would now be added:
        # (1, 1, '2023-05-04 08:00', null, 2, 1, 1)
        scheduled_trip = ww.schedule_trip(1, dt.datetime(2023, 5, 4, 8, 0))
        assert scheduled_trip, \
            f"[Schedule Trip] Expected True, Got {scheduled_trip}"

        # Can't schedule the same route of the same day.
        scheduled_trip = ww.schedule_trip(1, dt.datetime(2023, 5, 4, 13, 0))
        assert not scheduled_trip, \
            f"[Schedule Trip] Expected False, Got {scheduled_trip}"

        scheduled_trip = ww.schedule_trip(1, dt.datetime(2023, 5, 5, 15, 0))
        assert not scheduled_trip, \
            f"[Schedule Trip] Expected False, Got {scheduled_trip}"
        # -------------------- Testing schedule_trips  ------------------------#

        # All routes for truck tid are scheduled on that day
        # scheduled_trips = ww.schedule_trips(1, dt.datetime(2023, 5, 3))
        # assert scheduled_trips == 0, \
        #     f"[Schedule Trips] Expected 0, Got {scheduled_trips}"

        # ----------------- Testing update_technicians  -----------------------#

        # This uses the provided file. We recommend you make up your custom
        # file to thoroughly test your implementation.
        # You will need to check that data in the Technician relation has been
        # changed accordingly
        # qf = open('qualifications.txt', 'r')
        # updated_technicians = ww.update_technicians(qf)
        # assert updated_technicians == 2, \
        #     f"[Update Technicians] Expected 2, Got {updated_technicians}"

        # ----------------- Testing workmate_sphere ---------------------------#

        # This employee doesn't exist in our instance
        workmate_sphere = ww.workmate_sphere(2023)
        assert len(workmate_sphere) == 0, \
            f"[Workmate Sphere] Expected [], Got {workmate_sphere}"

        workmate_sphere = ww.workmate_sphere(3)
        # Use set for comparing the results of workmate_sphere since
        # order doesn't matter.
        # Notice that 2 is added to 1's work sphere because of the trip we
        # added earlier.
        assert set(workmate_sphere) == {1, 2}, \
            f"[Workmate Sphere] Expected {{1, 2}}, Got {workmate_sphere}"

        # ----------------- Testing schedule_maintenance ----------------------#

        # You will need to check the data in the Maintenance relation
        scheduled_maintenance = ww.schedule_maintenance(dt.date(2023, 5, 5))
        assert scheduled_maintenance == 7, \
            f"[Schedule Maintenance] Expected 7, Got {scheduled_maintenance}"

        # ------------------ Testing reroute_waste  ---------------------------#

        # There is no trips to facility 1 on that day
        reroute_waste = ww.reroute_waste(1, dt.date(2023, 5, 10))
        assert reroute_waste == 0, \
            f"[Reroute Waste] Expected 0. Got {reroute_waste}"

        # You will need to check that data in the Trip relation has been
        # changed accordingly
        reroute_waste = ww.reroute_waste(1, dt.date(2023, 5, 3))
        assert reroute_waste == 1, \
            f"[Reroute Waste] Expected 1. Got {reroute_waste}"
    finally:
        if qf and not qf.closed:
            qf.close()
        ww.disconnect()


if __name__ == '__main__':
    # Un comment-out the next two lines if you would like to run the doctest
    # examples (see ">>>" in the methods connect and disconnect)
    # import doctest
    # doctest.testmod()

    # TODO: Put your testing code here, or call testing functions such as
    #   this one:
    test_preliminary()
