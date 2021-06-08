    def rotate_point_2d(self, local_vector, global_vector, p):
        # local coodinate system and global coordinate system vectors that will be made to align with each other.
        # p is a point to be rotated along with this vector alignment.
        # This is in essence a 2D rotation in the plane formed by the two vectors and around the perpendicular to this plane.
        # (Two vectors have the origin in common and thus make three points altogether and this is a plane)
        # (The surface normal is the rotation axis and the angle of rotation is the angle between the two vectors in this plane)

        i = self.identity_matrix()

        v = self.cross_product(local_vector, global_vector)
        s = self.vector_magnitude(v)
        c = self.dot_product(local_vector, global_vector)

        vx = self.empty_matrix()
        vx[0][0] = 0.0
        vx[0][1] = -1.0 * v.z
        vx[0][2] = v.y

        vx[1][0] = v.z
        vx[1][1] = 0.0
        vx[1][2] = -1.0 * v.x

        vx[2][0] = -1.0 * v.y
        vx[2][1] = v.x
        vx[2][2] = 0.0

        v2x = self.scale_matrix(1 / (1 + c), self.matrix_product(vx, vx))

        # Now create the rotation matrix by adding these components
        r = self.matrix_add( self.matrix_add(i, vx), v2x)

        # Now do the rotation by multiplying this rotation matrix by the individual points (or vectors)
        return(point((p.x * r[0][0]) + (p.y * r[1][0]) + (p.z * r[2][0]),
                        (p.x * r[0][1]) + (p.y * r[1][1]) + (p.z * r[2][1]),
                        (p.x * r[0][2]) + (p.y * r[1][2]) + (p.z * r[2][2])))                        

    # This routine takes two sets of datums (local and global) and converts a newly recorded point
    # from the local coordinate system (e.g. Microscribe) to the global coordinate system.
    # It does this by performing a rotation around first one leg and then another of the triangle formed by the datums.
    # It is written to be readable.  Much efficiency could be gained but as points are only rotated as recorded,
    # the routine does not need to be fast.  Note too that all of the dependent routines are self written
    # rather than pulled from existing libraries (like numpy) to avoid dependencies.  Dependencies make porting to
    # Apple and Android more difficult.
    def rotate_point(self, p = None):
        # p is a point to be rotated

        if p is None:
            p = self.xyz

        if len(self.rotate_local) is 3 and len(self.rotate_global) is 3 and p is not None:
            rotated_local = []

            # Shift point to relative to the origin
            p = self.vector_subtract(p, self.rotate_local[0])

            # First line up one side of the triangle formed by the three datum points
            local_vector = self.normalize_vector(self.vector_subtract(self.rotate_local[1], self.rotate_local[0]))
            global_vector = self.normalize_vector(self.vector_subtract(self.rotate_global[1], self.rotate_global[0]))
            p_out = self.rotate_point_2d(global_vector, local_vector, p)

            # Put the local datums in this new space as well
            rotated_local.append(self.rotate_point_2d(global_vector, local_vector, self.rotate_local[0]))
            rotated_local.append(self.rotate_point_2d(global_vector, local_vector, self.rotate_local[1]))
            rotated_local.append(self.rotate_point_2d(global_vector, local_vector, self.rotate_local[2]))
            #rotated_local.append(self.rotate_point_2d(global_vector, local_vector, self.vector_subtract(self.rotate_local[2], self.rotate_local[0])))

            # Now line up on the other side of the triangle formed by the three datum points
            local_vector = self.normalize_vector(self.vector_subtract(rotated_local[2], rotated_local[0]))
            global_vector = self.normalize_vector(self.vector_subtract(self.rotate_global[2], self.rotate_global[0]))
            p_out2 = self.rotate_point_2d(global_vector, local_vector, p_out)

            # Finish the rotation for the local datums as well (not strictly needed for points 2 and 3)
            rotated_local[0] = self.rotate_point_2d(global_vector, local_vector, rotated_local[0])
            rotated_local[1] = self.rotate_point_2d(global_vector, local_vector, rotated_local[1])
            rotated_local[2] = self.rotate_point_2d(global_vector, local_vector, rotated_local[2])

            # Now align the starting points of each grid systems by shifting the first datum points onto each other
            datum_diff = self.vector_subtract(self.rotate_global[0], rotated_local[0])
            #result = self.translate_point(datum_diff, p_out2)
            result = self.translate_point(self.rotate_global[0], p_out2)

            return(result)

        else:
            return(None)

